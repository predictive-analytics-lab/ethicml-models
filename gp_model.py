"""Definitions of GP models"""
import gpytorch
from gpytorch.models import AbstractVariationalGP, ExactGP
from gpytorch.variational import CholeskyVariationalDistribution, VariationalStrategy

import utils


class Variational(AbstractVariationalGP):
    """GP using variational inference"""
    def __init__(self, _, inducing_inputs, __, flags):
        # define the variational distribution with the length of the inducing inputs
        variational_distribution = CholeskyVariationalDistribution(inducing_inputs.shape[0])

        # The variational strategy defines how the GP prior is computed and
        # how to marginalize out the inducing point function values
        variational_strategy = VariationalStrategy(self, inducing_inputs, variational_distribution,
                                                   learn_inducing_locations=flags.optimize_inducing)
        super().__init__(variational_strategy)
        # initialize mean and covariance
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(getattr(gpytorch.kernels, flags.cov)())

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        latent_pred = gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
        return latent_pred

    def get_marginal_log_likelihood(self, likelihood, num_data):
        """Get the marginal log likelihood function that works with the GP model"""
        return gpytorch.mlls.VariationalELBO(likelihood, self, num_data)


class Exact(ExactGP):
    """GP using exact inference"""
    def __init__(self, train_ds, _, likelihood, flags):
        train_x, train_y = utils.dataset2tensor(train_ds)
        super().__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(getattr(gpytorch.kernels, flags.cov)())

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        latent_pred = gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
        return latent_pred

    def get_marginal_log_likelihood(self, likelihood, _):
        """Get the marginal log likelihood function that works with the GP model"""
        return gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, self)


class ExactMultitask(ExactGP):
    """GP using exact inference with multi-dimensional output"""
    def __init__(self, train_ds, _, likelihood, flags):
        train_x, train_y = utils.dataset2tensor(train_ds)
        super().__init__(train_x, train_y, likelihood)
        num_tasks = train_y.size()[1]
        self.mean_module = gpytorch.means.MultitaskMean(gpytorch.means.ConstantMean(),
                                                        num_tasks=num_tasks)
        self.covar_module = gpytorch.kernels.MultitaskKernel(
            getattr(gpytorch.kernels, flags.cov)(), num_tasks=num_tasks, rank=1)

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        latent_pred = gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)
        return latent_pred

    def get_marginal_log_likelihood(self, likelihood, _):
        """Get the marginal log likelihood function that works with the GP model"""
        return gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, self)
