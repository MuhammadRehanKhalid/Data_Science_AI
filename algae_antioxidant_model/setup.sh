#!/bin/bash
echo "🔧 Setting up environment..."
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Setup complete"
