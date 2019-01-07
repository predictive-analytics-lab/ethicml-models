from pathlib import Path
import numpy as np

import metrics as metrics_module


def init_metrics(metric_flag):
    """Initialize metrics

    Args:
        metric_flag: a string that contains the names of the metrics separated with commas
        is_eager: True if in eager execution
    Returns:
        a dictionary with the initialized metrics
    """
    metrics = {}
    if metric_flag == "":
        return metrics  # No metric names given -> return empty dictionary

    # First, find all metrics
    dict_of_metrics = {}
    for class_name in dir(metrics_module):  # Loop over everything that is defined in `metrics`
        class_ = getattr(metrics_module, class_name)
        # Here, we filter out all functions and other classes which are not metrics
        if isinstance(class_, type(metrics_module.Metric)) and issubclass(
                class_, metrics_module.Metric):
            dict_of_metrics[class_.name] = class_

    if isinstance(metric_flag, list):
        metric_list = metric_flag  # `metric_flag` is already a list
    else:
        metric_list = metric_flag.split(',')  # Split `metric_flag` into a list
    for name in metric_list:
        try:
            # Now we can just look up the metrics in the dictionary we created
            metric = dict_of_metrics[name]
        except KeyError:  # No metric found with the name `name`
            raise ValueError(f"Unknown metric \"{name}\"")
        metrics[name] = metric()
    return metrics


def update_metrics(metrics, inputs, labels, pred_mean):
    """Update metrics

    Args:
        metrics: a dictionary with the initialized metrics
        features: the input
        labels: the correct labels
        pred_mean: the predicted mean
    """
    for metric in metrics.values():
        metric.update(inputs, labels, pred_mean)


def record_metrics(metrics, summary_writer=None, step_counter=None):
    """Print the result and record it in the summary if a summary writer is given

    Args:
        metrics: a dictionary with the updated metrics
    """
    for metric in metrics.values():
        result = metric.result()
        print(f"{metric.name}: {result}")
        if summary_writer is not None and step_counter is not None:
            summary_writer.add_scalar(metric.name, result, step_counter)


def save_predictions(pred_mean, pred_var, save_dir, flags):
    """Save predictions into a numpy file"""
    if flags.preds_path:
        working_dir = save_dir if flags.save_dir else Path(".")
        np.savez_compressed(working_dir / flags.preds_path, pred_mean=pred_mean, pred_var=pred_var)
        print(f"Saved in \"{str(working_dir / flags.preds_path)}\"")
