import numpy as np
import scipy.linalg
import torch

from fgel.abstract_estimation_method import AbstractEstimationMethod


class KernelVMM(AbstractEstimationMethod):
    def __init__(self, model, alpha, kernel_args=None, num_iter=2, verbose=False):
        AbstractEstimationMethod.__init__(self, model, kernel_args)
        self.alpha = alpha
        self.num_iter = num_iter
        self.verbose = verbose

    def _train_internal(self, x, z, x_val, z_val, debugging):
        alpha = self.alpha
        while True:
            try:
                self._try_fit_internal(x, z, x_val, z_val, alpha)
                did_succeed = self.model.is_finite()
            except:
                print(self.model.get_parameters())
                did_succeed = False

            if did_succeed or alpha > 10:
                break
            elif alpha == 0:
                alpha = 1e-8
            else:
                alpha *= 10

    def _try_fit_internal(self, x, z, x_val, z_val, alpha):
        x_tensor = self._to_tensor(x)

        self._set_kernel(z, z_val)

        for iter_i in range(self.num_iter):
            # obtain m matrix for this iteration, using current theta parameter
            m = self._to_tensor(self._calc_m_matrix(x_tensor, alpha))
            # re-optimize rho using LBFGS
            optimizer = torch.optim.LBFGS(
                self.model.parameters(), line_search_fn="strong_wolfe"
            )

            def closure():
                optimizer.zero_grad()
                psi_x = self.model.psi(x_tensor).transpose(1, 0).flatten()
                m_rho_x = torch.matmul(m, psi_x).detach()
                loss = 2.0 * torch.matmul(m_rho_x, psi_x)
                loss.backward()
                return loss

            optimizer.step(closure)

            if self.verbose and x_val is not None:
                val_mmr_loss = self._calc_val_mmr(x_val, z_val)
                print("iter %d, validation MMR: %e" % (iter_i, val_mmr_loss))

    def _calc_m_matrix(self, x_tensor, alpha):
        n = self.kernel_z.shape[0]
        k_z_m = np.stack([self.kernel_z for _ in range(self.psi_dim)], axis=0)
        psi_m = self.model.psi(x_tensor).detach().cpu().numpy()
        q = (k_z_m * psi_m.T.reshape(self.psi_dim, 1, n)).reshape(self.psi_dim * n, n)
        del psi_m

        q = (q @ q.T) / n
        l = scipy.linalg.block_diag(*k_z_m)
        del k_z_m
        q += alpha * l
        try:
            return l @ np.linalg.solve(q, l)
        except:
            return l @ np.linalg.lstsq(q, l, rcond=None)[0]


if __name__ == "__main__":
    from experiments.exp_heteroskedastic import run_heteroskedastic_n_times

    estimatorkwargs = dict(alpha=1e-6)
    results = run_heteroskedastic_n_times(
        theta=1.7,
        noise=1.0,
        n_train=200,
        repititions=20,
        estimatortype=KernelVMM,
        estimatorkwargs=estimatorkwargs,
    )
    print("Thetas: ", results["theta"])
