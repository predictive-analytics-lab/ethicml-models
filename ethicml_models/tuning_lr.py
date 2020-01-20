"""Interface to the TuningLr algorithm."""
from pathlib import Path
from typing import Dict, Union, Optional, List, NamedTuple

from ethicml.algorithms.inprocess import InAlgorithmAsync
from ethicml.algorithms.inprocess.shared import flag_interface
from ethicml.utility import PathTuple, TestPathTuple

from .common import ROOT_PATH

__all__ = ["EOFlags", "DPFlags", "TuningLr"]


class EOFlags(NamedTuple):
    p_ybary1_s0: float
    p_ybary1_s1: float
    p_ybary0_s0: float
    p_ybary0_s1: float
    biased_acceptance_s0: Optional[float] = None
    biased_acceptance_s1: Optional[float] = None


class DPFlags(NamedTuple):
    target_rate_s0: float
    target_rate_s1: float
    p_ybary0_or_ybary1_s0: float = 1.0
    p_ybary0_or_ybary1_s1: float = 1.0
    biased_acceptance_s0: Optional[float] = None
    biased_acceptance_s1: Optional[float] = None


class TuningLr(InAlgorithmAsync):
    def __init__(
        self,
        weight_decay=1e-1,
        batch_size=64,
        lr_decay=1.0,
        learning_rate=1e-3,
        epochs=100,
        fair=False,
        debiasing_args: Optional[Union[DPFlags, EOFlags]] = None,
        use_sgd=False,
        use_s=False,
        device="cpu",
        seed=42,
    ):
        super().__init__()
        self.flags: Dict[str, Union[bool, int, float, str]] = {
            "weight_decay": weight_decay,
            "batch_size": batch_size,
            "lr_decay": lr_decay,
            "learning_rate": learning_rate,
            "epochs": epochs,
            "use_sgd": use_sgd,
            "device": device,
            "use_s": use_s,
            "seed": seed,
        }
        if fair:
            assert debiasing_args is not None
            if isinstance(debiasing_args, DPFlags):
                self.flags.update(
                    {
                        "fairness": "DP",
                        "param1": debiasing_args.target_rate_s0,
                        "param2": debiasing_args.target_rate_s0,
                        "param3": debiasing_args.p_ybary0_or_ybary1_s0,
                        "param4": debiasing_args.p_ybary0_or_ybary1_s1,
                    }
                )
            else:
                self.flags.update(
                    {
                        "fairness": "EO",
                        "param1": debiasing_args.p_ybary1_s0,
                        "param2": debiasing_args.p_ybary1_s1,
                        "param3": debiasing_args.p_ybary0_s0,
                        "param4": debiasing_args.p_ybary0_s1,
                    }
                )
            if debiasing_args.biased_acceptance_s0 is not None:
                self.flags.update({"biased_acceptance_s0": debiasing_args.biased_acceptance_s0})
            if debiasing_args.biased_acceptance_s1 is not None:
                self.flags.update({"biased_acceptance_s1": debiasing_args.biased_acceptance_s1})

        # =================================== generate name =======================================
        self.__name = f"TuningLR, wd: {weight_decay}"
        if use_sgd:
            self.__name += ", SGD"
        else:
            self.__name += ", RAdam"
        if use_s:
            self.__name += ", use s"
        if fair:
            assert debiasing_args is not None
            if isinstance(debiasing_args, DPFlags):
                self.__name += f", PR_t: {debiasing_args.target_rate_s0}"
            else:
                self.__name += f", TPR_t: {debiasing_args.p_ybary1_s0}"
                self.__name += f", TNR_t: {debiasing_args.p_ybary0_s0}"

    @property
    def name(self):
        return self.__name

    def _script_command(
        self, train_paths: PathTuple, test_paths: TestPathTuple, pred_path: Path
    ) -> List[str]:
        cmds = flag_interface(train_paths, test_paths, pred_path, self.flags)
        return [str(ROOT_PATH / "implementations" / "run_tuning_lr.py")] + cmds