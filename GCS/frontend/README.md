# Auto-Start Configuration

## Quick Start (Recommended)

### Start Both Applications (Default)
```bash
cd GCS/frontend
npm run dev
```
This starts both GCS (port 8765) and RecordingAnalysis (port 9876) with colored output.

### Start Only GCS
```bash
cd GCS/frontend
npm run dev:gcs-only
```
This starts only the GCS application on port 8765.

## Individual Application Start

### Start only RecordingAnalysis
```bash
cd RecordingAnalysis
npm run dev
```

## Application URLs

- **GCS Frontend**: http://localhost:8765
- **RecordingAnalysis**: http://localhost:9876

## Setup Instructions

1. **Install dependencies for GCS:**
   ```bash
   cd GCS/frontend
   npm install
   ```

2. **Install dependencies for RecordingAnalysis:**
   ```bash
   cd RecordingAnalysis
   npm install
   ```

## Available Commands
From `GCS/frontend` directory:

- `npm run dev` - **Start both GCS and RecordingAnalysis** (default)
- `npm run dev:gcs-only` - Start only GCS
- `npm run build` - Build GCS for production
- `npm run start` - Start GCS in production mode
- `npm run lint` - Run ESLint

The applications will start with colored output:
- 🔵 **Blue**: GCS Frontend logs  
- 🟢 **Green**: RecordingAnalysis logs