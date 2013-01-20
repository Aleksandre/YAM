import sys
sys.path.append("yam")
import config

def test_config_man():
    config.setConfigFolder("./")
    assert config.getConfigFolder() == "./" 

    config.setProperty("test-property", "test-value")
    assert config.getProperty("test-property") == "test-value"
    config.deleteConfigFile()