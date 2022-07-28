#!/usr/bin/env python
"""Main script."""
import argparse
import logging
import sys
from pathlib import Path

from rich.logging import RichHandler
from rich.traceback import install

from . import _version
from bidsmreye.combine import combine
from bidsmreye.generalize import generalize
from bidsmreye.prepare_data import prepare_data
from bidsmreye.utils import Config

__version__ = _version.get_versions()["version"]

# let rich print the traceback
install(show_locals=True)

# log format
FORMAT = "bidsMReye - %(asctime)s - %(levelname)s - %(message)s"


def main(argv=sys.argv) -> None:
    """Execute the main script."""
    parser = argparse.ArgumentParser(
        description="BIDS app using deepMReye to decode eye motion for fMRI time series data."
    )
    parser.add_argument(
        "bids_dir",
        help="""
        The directory with the input dataset formatted according to the BIDS standard.
        """,
    )
    parser.add_argument(
        "output_dir",
        help="""
        The directory where the output files will be stored.
        """,
    )
    parser.add_argument(
        "analysis_level",
        help="""Level of the analysis that will be performed.
        Multiple participant level analyses can be run independently (in parallel)
        using the same output_dir.
        """,
        choices=["participant"],
    )
    parser.add_argument(
        "--action",
        help="""
        What action to perform:
        - prepare: prepare data for analysis coregister to template,
                   normalize and extract data
        - combine: combine data labels and data from different runs into a single file
        - generalize: generalize from data to give predicted labels
        """,
        choices=["all", "prepare", "combine", "generalize"],
        default="all",
    )
    parser.add_argument(
        "--participant_label",
        help="""
        The label(s) of the participant(s) that should be analyzed.
        The label corresponds to sub-<participant_label> from the BIDS spec
        (so it does not include "sub-").
        If this parameter is not provided, all subjects will be analyzed.
        Multiple participants can be specified with a space separated list.
        """,
        nargs="+",
    )
    parser.add_argument(
        "-t",
        "--task",
        help="""
        The label of the task that will be analyzed.
        The label corresponds to task-<task_label> from the BIDS spec
        so it does not include "task-").
        """,
        nargs="+",
    )
    parser.add_argument(
        "-r",
        "--run",
        help="""
        The label of the run that will be analyzed.
        The label corresponds to run-<task_label> from the BIDS spec
        so it does not include "run-").
        """,
        nargs="+",
    )
    parser.add_argument(
        "-s",
        "--space",
        help="""
        The label of the space that will be analyzed.
        The label corresponds to space-<space_label> from the BIDS spec
        (so it does not include "space-").
        """,
        nargs="+",
    )
    parser.add_argument(
        "-m",
        "--model",
        help="model to use",
        choices=["guided_fixations"],
        default="guided_fixations",
    )
    parser.add_argument(
        "--verbosity",
        help="INFO, WARNING. Defaults to INFO",
        choices=["INFO", "WARNING"],
        default="INFO",
    )
    parser.add_argument(
        "--debug",
        help="true or false. Defaults to False",
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "--reset_database",
        help="""
        Resets the database of the input dataset.
        Values: true or false. Defaults to false.
        """,
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="show program's version number and exit",
        version=f"\nbidsMReye version {__version__}\n",
    )
    # --bids-filter-file
    # --reset_database

    args = parser.parse_args(argv[1:])

    if args.model in {"guided_fixations", "", None}:
        model_weights_file = Path.cwd().joinpath(
            "models",
            "dataset1_guided_fixations.h5",
        )

    cfg = Config(
        args.bids_dir,
        args.output_dir,
        participant=args.participant_label or None,
        task=args.task or None,
        run=args.run or None,
        space=args.space or None,
        debug=args.debug,
        model_weights_file=model_weights_file,
        reset_database=args.reset_database,
    )

    log_level = "DEBUG" if cfg.debug else args.verbosity or "INFO"
    logging.basicConfig(
        level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    log = logging.getLogger("rich")

    log.info("Running bidsmreye version %s", __version__)

    if cfg.debug:
        log.debug("DEBUG MODE")

    if cfg.model_weights_file not in {"", None}:
        assert Path(cfg.model_weights_file).is_file()
        log.info(f"Using model: {cfg.model_weights_file}")

    if args.analysis_level == "participant":

        if args.action == "all":
            log.info("PREPARING DATA")
            prepare_data(cfg)
            log.info("COMBINING DATA")
            combine(cfg)
            log.info("GENERALIZING")
            generalize(cfg)

        elif args.action == "prepare":
            log.info("PREPARING DATA")
            prepare_data(cfg)

        elif args.action == "combine":
            log.info("COMBINING DATA")
            combine(cfg)

        elif args.action == "generalize":
            log.info("GENERALIZING")
            generalize(cfg)

        else:
            log.error("Unknown action")
            sys.exit(1)


if __name__ == "__main__":
    main()
