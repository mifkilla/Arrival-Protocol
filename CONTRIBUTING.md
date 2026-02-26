# Contributing to ARRIVAL Protocol

Thank you for your interest in contributing to the ARRIVAL Protocol!

## How to Contribute

### Reporting Issues
- Use GitHub Issues for bug reports and feature requests
- Include your Python version, OS, and relevant error messages
- For experiment reproducibility issues, include your API configuration (without keys!)

### Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the code style below
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

### Code Style
- Follow PEP 8
- All new files must include the AGPL-3.0-or-later license header
- Use type hints where practical
- Write docstrings for public functions

### Running Tests
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Adding New Experiments
1. Create a new directory under `experiments/`
2. Include `config_phaseNN.py` and `run_phaseNN.py`
3. Document the experiment design in a docstring
4. Save results to `results/phase_NN/`

## License

By contributing, you agree that your contributions will be licensed under:
- **Code:** AGPL-3.0-or-later
- **Documentation:** CC BY-NC 4.0

## Contact

- Author: Mefodiy Kelevra
- ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
