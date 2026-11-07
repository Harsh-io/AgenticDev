import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import config

def test_config_groq_model():
    assert hasattr(config, "GROQ_MODEL")
    assert config.GROQ_MODEL != ""

def test_config_frontend_origin():
    assert hasattr(config, "FRONTEND_ORIGIN")
    assert "localhost" in config.FRONTEND_ORIGIN

