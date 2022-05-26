import argparse
import json
import os

import numpy as np
import torch


def run_experiment(experiment, exp_params, n_train, estimator_class, estimator_kwargs=None,
                   hyperparams=None, validation_metric='mmr', seed0=12345):
    """
    Runs experiment with specified estimator and choice of hyperparams and returns the best model and the
    corresponding error measures.
    """
    if estimator_kwargs is None:
        estimator_kwargs = {}
    if hyperparams is None or hyperparams == {}:
        hyperparams = {None: [None]}
    hypervals = list(hyperparams.values())[0]
    hyperparam = list(hyperparams.keys())[0]

    np.random.seed(seed0)
    torch.random.manual_seed(seed0+1)
    exp = experiment(**exp_params)
    exp.setup_data(n_train=n_train, n_val=n_train, n_test=20000)

    train_risks = []
    test_risks = []
    mses = []
    val_mmr = []
    params = []
    models = []
    for hyperval in hypervals:
        model = exp.init_model()
        if hyperval is None:
            estimator = estimator_class(model=model, **estimator_kwargs)
        else:
            hparam = {hyperparam: hyperval}
            estimator = estimator_class(model=model, **hparam, **estimator_kwargs)
        estimator.train(exp.x_train, exp.z_train, exp.x_val, exp.z_val)

        models.append(model)

        params.append(float(np.squeeze(model.get_parameters())))
        train_risks.append(float(exp.eval_test_risk(model, exp.x_train)))
        test_risks.append(float(exp.eval_test_risk(model, exp.x_test)))
        mses.append(float(np.mean(np.square(np.squeeze(model.get_parameters()) - np.squeeze(exp.get_true_parameters())))))
        val_mmr.append(float(estimator.calc_val_mmr(exp.x_val, exp.z_val).detach().numpy()))
    if validation_metric == 'mmr' and len(models) > 1:
        val_mmr = np.nan_to_num(val_mmr, nan=np.inf)
        i = np.argmin(val_mmr)
    else:
        i = 0
    stats = {'hyperparam': hypervals[i],
             'param': params[i],
             'train_risk': train_risks[i],
             'test_risk': test_risks[i],
             'mse': mses[i],
             'val_mmr': val_mmr[i]}
    return models[i], stats


def run_experiment_repeated(experiment, exp_params, n_train, estimator_class, estimator_kwargs, hyperparams,
                            repititions, seed0=12345, filename=None):
    """
    Runs the same experiment `repititions` times and computes statistics.
    """
    hypervals = []
    train_risk = []
    test_risk = []
    mse = []
    val_mmr = []

    for i in range(repititions):
        _, stats = run_experiment(experiment=experiment, exp_params=exp_params, n_train=n_train,
                                  estimator_class=estimator_class, estimator_kwargs=estimator_kwargs,
                                  hyperparams=hyperparams, validation_metric='mmr', seed0=seed0+i)

        hypervals.append(stats['hyperparam'])
        train_risk.append(stats['train_risk'])
        test_risk.append(stats['test_risk'])
        mse.append(stats['mse'])
        val_mmr.append(stats['val_mmr'])

    results = {"mean_square_error": np.mean(mse),
                "std_square_error": np.std(mse),
                "max_square_error": np.max(mse),
                "mean_risk": np.mean(test_risk),
                "std_risk": np.std(test_risk),
                "max_risk": np.max(test_risk),
                "mean_mmr_loss": np.mean(val_mmr),
                "std_mmr_loss": np.std(val_mmr),
                "n_runs": repititions,
                "hyperparam_values": hypervals,
                "train_risks": train_risk,
               
               }

    if filename is not None:
        prefix = f"results/{str(experiment.__name__)}/{str(experiment.__name__)}_method={str(estimator_class.__name__)}_n={n_train}"
        os.makedirs(os.path.dirname(prefix), exist_ok=True)
        with open(prefix + filename + ".json", "w") as fp:
            json.dump(results, fp)
    return results


def run_all(experiment, repititions, method=None):
    """
    Runs all methods for all sample sizes `n_train_list` sequentially `repititions` times. This can be used if one has
    only access to a single machine instead of a computer cluster. Might take a long time to finish.
    """
    from exp_config import methods, experiments

    exp_info = experiments[experiment]

    if method is not None:
        methods = {method: methods[method]}

    for n_train in exp_info['n_train']:
        for method, estimator_info in methods.items():
            print(f'Running {method} with n_train={n_train}.')
            run_experiment_repeated(experiment=exp_info['exp_class'],
                                    exp_params=exp_info['exp_params'],
                                    n_train=n_train,
                                    estimator_class=estimator_info['estimator_class'],
                                    estimator_kwargs=estimator_info['estimator_kwargs'],
                                    hyperparams=estimator_info['hyperparams'],
                                    repititions=repititions,
                                    filename='')


if __name__ == "__main__":
    from exp_config import methods, experiments

    parser = argparse.ArgumentParser()
    parser.add_argument('--run_all', action='store_true')
    parser.add_argument('--experiment', type=str, default='heteroskedastic')
    parser.add_argument('--n_train', type=int, default=100)
    parser.add_argument('--method', type=str, default='OrdinaryLeastSquares')
    parser.add_argument('--rollouts', type=int, default=1)
    parser.add_argument('--filename', type=str, default='')

    args = parser.parse_args()

    estimator_info = methods[args.method]
    exp_info = experiments[args.experiment]

    if args.run_all:
        run_all(args.experiment, args.rollouts, args.method)
    else:
        results = run_experiment_repeated(experiment=exp_info['exp_class'],
                                          exp_params=exp_info['exp_params'],
                                          n_train=args.n_train,
                                          estimator_class=estimator_info['estimator_class'],
                                          estimator_kwargs=estimator_info['estimator_kwargs'],
                                          hyperparams=estimator_info['hyperparams'],
                                          repititions=args.rollouts,
                                          filename=args.filename)
        print(results)