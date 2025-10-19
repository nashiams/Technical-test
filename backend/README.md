## Setup

### Download Required Model File

The face swap model is not included in the repository due to size constraints.

Download it manually:

```bash
cd backend
wget https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx

# Or download from: https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx
```

Place it at: `backend/inswapper_128.onnx`

The file is already in `.gitignore` and will not be committed.

## Docker Setup

```bash
docker-compose up -d
```

The model file will be mounted into the worker container.
