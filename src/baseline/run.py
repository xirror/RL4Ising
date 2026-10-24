import argparse
from pathlib import Path

from utils import base64_encode, read_nxgraph
from scip import solve


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


def run_single_file(input_path, time_limit=3600, out_dir="results"):
    input_path = Path(input_path)
    output_path = Path(out_dir) / f"{input_path.stem}.txt"
    graph = read_nxgraph(str(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = solve(graph, time_limit, output_path.with_suffix(".log"))
    write_result(result, output_path)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run baseline solver on graphs.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/tutorials/VCA/dataset/EA/EA_10x10/10x10_uniform_seed1.txt"],
        help="One or more files or directories (all .txt files, non-recursive). Defaults to a specific test file if omitted.",
    )
    
    parser.add_argument(
        "--solver", 
        required=True,
        choices=["scip"]
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

    for path in args.paths:
        input_path = Path(path)
        files = [path]
        if input_path.is_dir():
            files = sorted(file for file in input_path.glob("*.txt") if file.is_file())
        for file in files:
            run_single_file(file, args.time_limit, args.out_dir)


if __name__ == "__main__":
    main()
