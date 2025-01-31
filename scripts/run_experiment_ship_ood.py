import argparse
import json
import os
import pathlib

from deepsysid.pipeline.configuration import ExperimentConfiguration, ExperimentGridSearchTemplate
from deepsysid.pipeline.evaluation import evaluate_model
from deepsysid.pipeline.testing.runner import test_model

from relinet.utils import load_environment, retrieve_tested_models, get_configuration_path


def main():
    parser = argparse.ArgumentParser('Run experiments for the 4-DOF ship in-distribution dataset.')
    parser.add_argument('device')
    args = parser.parse_args()

    device_idx = int(args.device)

    main_path = pathlib.Path(__file__).parent.parent.absolute()
    report_path = main_path.joinpath('configuration').joinpath('progress-ship.json')
    environment_path = main_path.joinpath('environment').joinpath('ship-ood.env')
    environment = load_environment(environment_path)

    configuration_path = get_configuration_path(environment_file_path=environment_path)
    with configuration_path.open(mode='r') as f:
        configuration = ExperimentConfiguration.from_grid_search_template(
            ExperimentGridSearchTemplate.parse_obj(json.load(f))
        )

    models = retrieve_tested_models(report_path)
    print(
        'Found the following models to test on out-of-distribution '
        f'dataset: {", ".join(models)}.'
    )

    if configuration.session is None:
        n_runs = 1
    else:
        n_runs = configuration.session.total_runs_for_best_models

    for model_idx, model in enumerate(models):
        print(
            f'Testing {model} on out-of-distribution data ({model_idx}/{len(models)}).'
        )
        test_model(
            model_name=model,
            configuration=configuration,
            device_name=f'cuda:{device_idx}',
            mode='test',
            dataset_directory=environment['DATASET_DIRECTORY'],
            result_directory=environment['RESULT_DIRECTORY'],
            models_directory=environment['MODELS_DIRECTORY']
        )
        evaluate_model(
            model_name=model,
            config=configuration,
            mode='test',
            result_directory=environment['RESULT_DIRECTORY']
        )
        print(
            f'Finished test run 1/{n_runs}.'
        )
        for run_idx in range(1, n_runs):
            result_directory = os.path.join(
                environment['RESULT_DIRECTORY'],
                f'repeat-{run_idx}'
            )
            models_directory = os.path.join(
                environment['MODELS_DIRECTORY'],
                f'repeat-{run_idx}'
            )

            test_model(
                model_name=model,
                configuration=configuration,
                device_name=f'cuda:{device_idx}',
                mode='test',
                dataset_directory=environment['DATASET_DIRECTORY'],
                result_directory=result_directory,
                models_directory=models_directory
            )
            evaluate_model(
                model_name=model,
                config=configuration,
                mode='test',
                result_directory=result_directory
            )
            print(
                f'Finished test run {run_idx + 1}/{n_runs}.'
            )


if __name__ == '__main__':
    main()
