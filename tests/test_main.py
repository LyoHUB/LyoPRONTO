"""Tests for the high-level API (formerly main.py)."""

from contextlib import chdir
import pytest
import numpy as np
from lyopronto import *
from .utils import (
    assert_physically_reasonable_output,
    assert_complete_drying, 
    assert_incomplete_drying,
)

class TestHighLevelAPI:
    """Tests for the high-level API functions in lyopronto.high_level."""

    @pytest.mark.main
    def test_freezing_fullstack(self, mocker, repo_root, tmp_path):
        input_file = repo_root / "test_data" / "example_freezing.yaml"
        mocked_func = mocker.patch("lyopronto.freezing.freeze", wraps=freezing.freeze, autospec=True)
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            assert mocked_func.call_count == 1

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()


    @pytest.mark.main
    def test_knownRp_fullstack(self, mocker, repo_root, tmp_path):
        input_file = repo_root / "test_data" / "example_knownRp.yaml"
        mocked_func = mocker.patch("lyopronto.calc_knownRp.dry", wraps=calc_knownRp.dry, autospec=True)
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            assert mocked_func.call_count == 1

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()
            assert (tmp_path / "lyo_Pressure_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DryingProgress_testtime.pdf").exists()

    @pytest.mark.main
    def test_unknownKv_fullstack(self, mocker, repo_root, tmp_path, capsys):
        input_file = repo_root / "test_data" / "example_unknownKv.yaml"
        mocked_func = mocker.patch("lyopronto.calc_knownRp.dry", wraps=calc_knownRp.dry, autospec=True)
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            captured = capsys.readouterr()
            assert "Optimal Kv: " in captured.out
            assert mocked_func.call_count > 2 # Should be called multiple times by rootfinder

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()
            assert (tmp_path / "lyo_Pressure_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DryingProgress_testtime.pdf").exists()

    @pytest.mark.main
    def test_design_space_fullstack(self, repo_root, tmp_path):
        input_file = repo_root / "test_data" / "example_design_space.yaml"
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_DesignSpace_ProductTemperature_testtime.pdf").exists()
            assert (tmp_path / "lyo_DesignSpace_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DesignSpace_DryingTime_testtime.pdf").exists()




