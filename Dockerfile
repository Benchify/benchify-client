# Start with an alpine base image
FROM python:3.9-alpine

# Install necessary dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Create a working directory
WORKDIR /app

# Install Python dependencies
RUN pip install \
    auth0-python \
    appdirs \
    "pyjwt>=2.8.0" \
    requests \
    rich \
    typer \
    "urllib3==1.26.6" \
    stdlib_list \
    pytest \
    setuptools

# Create the test.py file
RUN echo -e "import numpy as np\n\n\
def swap_rows(matrix: np.ndarray, row1: int, row2: int) -> np.ndarray:\n\
    matrix[row1], matrix[row2] = matrix[row2], matrix[row1]\n\
    return matrix" > test.py

# Copy the source_manipulation.py into the image
COPY benchify/source_manipulation.py .

# Define the entry point
ENTRYPOINT ["python", "-c", "import sys; sys.path.insert(0, '/app'); from source_manipulation import get_pip_imports_recursive; print(get_pip_imports_recursive('test.py'))"]
