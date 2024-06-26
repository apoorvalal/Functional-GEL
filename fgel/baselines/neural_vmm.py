import numpy as np
import torch

from fgel.neural_fgel import NeuralFGEL


class NeuralVMM(NeuralFGEL):
    def __init__(self, kernel_lambda=0, **kwargs):
        super().__init__(divergence="off", **kwargs)
        self.kernel_lambda = kernel_lambda

    def objective(self, x, z, *args):
        f_of_z = self.dual_func(z)
        m_vector = (self.model.psi(x) * f_of_z).sum(1)
        moment = m_vector.mean()
        ow_reg = 0.25 * (m_vector**2).mean()
        if self.kernel_lambda > 0:
            k_reg_list = []
            for i in range(self.psi_dim):
                l_f = self.kernel_z.detach().numpy()
                w = np.linalg.solve(l_f, f_of_z[:, i].detach().cpu().numpy())
                w = self._to_tensor(w)
                k_reg_list.append((w * f_of_z[:, i]).sum())
            k_reg = 2 * self.kernel_lambda * torch.cat(k_reg_list, dim=0).sum()
        else:
            k_reg = 0
        if self.l2_lambda > 0:
            l_reg = self.l2_lambda * (f_of_z**2).mean()
        else:
            l_reg = 0
        return moment, -moment + ow_reg + k_reg + l_reg


if __name__ == "__main__":
    from experiments.exp_heteroskedastic import run_heteroskedastic_n_times

    estimatorkwargs = dict(
        max_num_epochs=50000,
        eval_freq=2000,
    )
    results = run_heteroskedastic_n_times(
        theta=1.7,
        noise=1.0,
        n_train=2000,
        repititions=2,
        estimatortype=NeuralVMM,
        estimatorkwargs=estimatorkwargs,
    )
    print("Thetas: ", results["theta"])
