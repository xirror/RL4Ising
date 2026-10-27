import argparse
import csv
from importlib import import_module
from pathlib import Path

from .utils import base64_encode, read_nxgraph


def write_result(result, output_path, print_terminal=True):
    bits = result["bits"]
    fields = {
        "Status": result["status"],
        "Objective Value": result["objective"],
        "Objective Bound": result["bound"],
        "Duration": result["duration"],
        "Time Limit": result["time_limit"],
        "MIP Gap": result["gap"],
        "Best Solution Encoded": base64_encode(bits) if bits else None,
        "Best Solution Raw": bits,
    }
    text = "".join(
        f"{name}: {value if value is not None else 'N/A'}\n"
        for name, value in fields.items()
    )
    Path(output_path).write_text(text)
    if print_terminal:
        print(text)


def run_single_file(input_path, time_limit=3600, out_dir="results", solver="scip"):
    adapter = import_module(f".{solver}", package=__spec__.parent)
    
    input_path = Path(input_path)
    output_path = Path(out_dir) / f"{input_path.stem}.txt"
    log_path = output_path.with_suffix(".log")

    if input_path.resolve() in (output_path.resolve(), log_path.resolve()):
        raise ValueError(f"Output would overwrite input: {input_path}")
    
    graph = read_nxgraph(str(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = adapter.solve(graph, time_limit, log_path)
    write_result(result, output_path)
    return result







def prepare_runs(paths, out_dir):
    out_dir = Path(out_dir).resolve()
    jobs = []
    inputs = set()
    outputs = {(out_dir / "baseline_results.csv").resolve()}
    seen = set()

    for path in paths:
        source = Path(path).resolve()
        is_directory = source.is_dir()
        output_is_subdirectory = (
            is_directory
            and out_dir != source
            and out_dir.is_relative_to(source)
        )
        files = sorted(source.rglob("*.txt")) if is_directory else [source]

        for file in files:
            if is_directory and not file.is_file():
                continue

            resolved_file = file.resolve()

            # Skip saved results in the output folder.
            if output_is_subdirectory and resolved_file.is_relative_to(out_dir):
                continue
            
            # Keep the same input folder structure in the results.
            relative = file.relative_to(source) if is_directory else Path(file.name)
            target = (out_dir / relative).with_suffix(".txt")
            input_output_pair = (resolved_file, target.resolve())

            if input_output_pair in seen:
                continue
            seen.add(input_output_pair)
            inputs.add(resolved_file)

            # Prevent different graphs from writing to the same result files.
            for output in (target, target.with_suffix(".log")):
                output = output.resolve()
                if output in outputs:
                    raise ValueError(f"Output collision: {output}")
                outputs.add(output)

            jobs.append((file, target.parent))

    # Check every output path before any solver starts.
    for output in outputs:
        if output in inputs:
            raise ValueError(f"Output would overwrite input: {output}")

        if any(parent in outputs for parent in output.parents):
            raise ValueError(f"Output file conflicts with an output directory: {output}")

        if output.is_dir() or any(parent.is_file() for parent in output.parents):
            raise ValueError(f"Output path is blocked: {output}")

    return jobs


def run_batch(jobs, solver, time_limit, out_dir):
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = ("input_path", "solver", "status", "objective", "bound", "duration", "time_limit", "gap")
    csv_path = output_dir / "baseline_results.csv"
    
    with csv_path.open("w", newline="", encoding="utf-8") as stream:

        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        stream.flush()
        
        for file, graph_out_dir in jobs:
            result = run_single_file(file, time_limit, graph_out_dir, solver)
            writer.writerow({
                "input_path": str(file.resolve()),
                "solver": solver,
                "status": result["status"],
                "objective": result["objective"],
                "bound": result["bound"],
                "duration": result["duration"],
                "time_limit": result["time_limit"],
                "gap": result["gap"],
            })
            stream.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run baseline solver on graphs.")
    
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/tutorials/VCA/dataset/EA/EA_10x10/10x10_uniform_seed1.txt"],
        help="One or more files or directories (recursively process .txt files). Defaults to a specific test file if omitted.",
    )
    
    parser.add_argument(
        "-s",
        "--solver", 
        required=True,
        choices=["scip", "gurobi"]
    )
    
    parser.add_argument(
        "-t", 
        "--time-limit", 
        type=int, 
        default=3600,
        help="Time limit for the solver in seconds (default: 3600).",
    )
    
    parser.add_argument(
        "-o", 
        "--out-dir", 
        default="results",
        help="Output directory for logs and individual text summaries (default: results).",
    )
    
    args = parser.parse_args(argv)

    jobs = prepare_runs(args.paths, args.out_dir)
    run_batch(jobs, args.solver, args.time_limit, args.out_dir)


if __name__ == "__main__":
    main()
