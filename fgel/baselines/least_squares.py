from fgel.abstract_estimation_method import AbstractEstimationMethod
import torch


class OrdinaryLeastSquares(AbstractEstimationMethod):
    def __init__(self, model):
        AbstractEstimationMethod.__init__(self, model)

    def _train_internal(self, x, z, x_dev, z_dev, debugging):
        x_tensor = self._to_tensor(x)
        z_tensor = self._to_tensor(z)
        n_sample = z_tensor.shape[0]

        optimizer = torch.optim.LBFGS(
            self.model.parameters(), line_search_fn="strong_wolfe"
        )

        def closure():
            optimizer.zero_grad()
            psi = self.model.psi(x_tensor)
            loss = torch.einsum("ir, ir -> ", psi, psi) / n_sample
            loss.backward()
            return loss

        optimizer.step(closure)


if __name__ == "__main__":
    from experiments.exp_heteroskedastic import run_heteroskedastic_n_times

    results = run_heteroskedastic_n_times(
        theta=1.7,
        noise=1.0,
        n_train=200,
        repititions=20,
        estimatortype=OrdinaryLeastSquares,
    )
    print("Thetas: ", results["theta"])
