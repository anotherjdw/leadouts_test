"""Glue entry point of the leadouts_summary ETL job.

Scaffold-owned: `generate create-job` renders it from the job spec, and it is uploaded
unchanged as the Glue job's script.
"""

from leadouts_test.jobs.leadouts_summary import (
    leadouts_summary_transformations as job,
)
from leadouts_test.runtime.job_settings import job_run, phase
from leadouts_test.utils.python import resolve_processing_dates


def run() -> None:
    """Parse arguments and resolve dates, then read, transform and write once."""
    args = job.parse_arguments()
    processing_dates = resolve_processing_dates(
        processing_type=args.PROCESSING_TYPE,
        lookback_days=args.LOOKBACK_DAYS,
        start_date=args.START_DATE,
        end_date=args.END_DATE,
    )
    with job_run("leadouts_summary", args, processing_dates) as record:
        with phase(record, "read"):
            sources = job.read(args, processing_dates)
        with phase(record, "transform"):
            output = job.transform(**sources)
        with phase(record, "write"):
            job.write(output, args.OUTPUT_PATH)


if __name__ == "__main__":
    run()
