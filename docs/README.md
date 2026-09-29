# Reinforcement Learning for Ising Models Documentation

## Structure

The documentation is organized as follows:

- **Home**: Homepage with links to documentation
- **[User Documentation](source/user/)**: Overview of project, usage, and motivation beind our work.

Each folder contains either .rst or .nblink files that can be modified to change the content on the site.

Alternatively, you can clone this repository and build the documentation locally, using conda:

```bash
# Clone the repository
git clone https://github.com/Open-Finance-Lab/RL4Ising.git

# Navigate to the docs folder
cd docs

# Install dependencies
conda env create --file environment.yml

# Activate environment  
conda activate rl4ising-docs

# Build the documentation
sphinx-build -b html -n source/ build/
```

The output HTML files will be located in the `build/` directory.

To preview the documentation locally, start a web server from the `docs` folder:

```bash
python -m http.server 8000 --directory build
```

Then open http://localhost:8000 in your browser. Press `Ctrl+C` in the terminal to stop the server.
