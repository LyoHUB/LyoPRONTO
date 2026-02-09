"""Tests for the high-level API (formerly main.py)."""

from contextlib import chdir
import pytest
import numpy as np
from lyopronto import *

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
        input_file = repo_root / "test_data" / "example_knownrp.yaml"
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
        input_file = repo_root / "test_data" / "example_unknownkv.yaml"
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
    def test_unknownkv_edgecases(self, repo_root, capsys):
        input_file = repo_root / "test_data" / "badexample_unknownkvrp.yaml"
        inputs = read_inputs(input_file)
        with pytest.raises(ValueError, match="Kv or Rp must be specified."):
            execute_simulation(inputs)

        # Check that if bracket is below, returns max
        inputs["sim"]["Rp_known"] = True
        inputs["Kv_range"] = [1e-5, 2e-5]
        with pytest.warns(UserWarning, match="bracket"):
            execute_simulation(inputs)
        captured = capsys.readouterr()
        assert f"Optimal Kv: {2e-5}" in captured.out
        
        # Check that if bracket is above, returns min
        inputs["sim"]["Rp_known"] = True
        inputs["Kv_range"] = [1e-3, 2e-3]
        with pytest.warns(UserWarning, match="bracket"):
            execute_simulation(inputs)
        captured = capsys.readouterr()
        assert f"Optimal Kv: {1e-3}" in captured.out

    @pytest.mark.main
    def test_unknown_rp_fullstack(self, mocker, repo_root, tmp_path, capsys):
        """Test that this function is called from high-level API without errors."""
        input_file = repo_root / "test_data" / "example_unknownrp.yaml"
        inputs = read_inputs(input_file)
        data = np.loadtxt(repo_root / "test_data" / "temperature.txt")
        inputs["time_data"] = data[:, 0]
        inputs["temp_data"] = data[:, 1]

        mocked_func = mocker.patch("lyopronto.calc_unknownRp.dry", wraps=calc_unknownRp.dry)

        output = execute_simulation(inputs)

        assert mocked_func.call_count == 1

        with chdir(tmp_path):

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()
            assert (tmp_path / "lyo_Rp_data_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Rp_Fit_testtime.pdf").exists()
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()
            assert (tmp_path / "lyo_Pressure_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DryingProgress_testtime.pdf").exists()


    @pytest.mark.main
    def test_design_space_fullstack(self, repo_root, tmp_path):
        input_file = repo_root / "test_data" / "example_design_space.yaml"
        inputs = read_inputs(input_file)
        with chdir(tmp_path):

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
    
    @pytest.mark.main
    def test_optimizer_novariable(self, repo_root, tmp_path):
        input_file = repo_root / "test_data" / "badexample_optimizer_noopt.yaml"
        with chdir(tmp_path):
            inputs = read_inputs(input_file)
            with pytest.raises(ValueError, match="Either Tsh or Pch needs to be variable to optimize."):
                execute_simulation(inputs)
    
    
    @pytest.mark.main
    def test_opt_tsh_fullstack(self, mocker, repo_root, tmp_path, capsys):
        input_file = repo_root / "test_data" / "example_opt_tsh.yaml"
        mocked_func = mocker.patch("lyopronto.opt_Tsh.dry", wraps=opt_Tsh.dry, autospec=True)
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
    def test_opt_pch_tsh_fullstack(self, mocker, repo_root, tmp_path, capsys):
        input_file = repo_root / "test_data" / "example_opt_pch_tsh.yaml"
        mocked_func = mocker.patch("lyopronto.opt_Pch_Tsh.dry", wraps=opt_Pch_Tsh.dry, autospec=True)
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            assert mocked_func.call_count == 1 # Should be called multiple times by rootfinder

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()
            assert (tmp_path / "lyo_Pressure_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DryingProgress_testtime.pdf").exists()

    @pytest.mark.main
    def test_opt_pch_fullstack(self, mocker, repo_root, tmp_path, capsys):
        input_file = repo_root / "test_data" / "example_opt_pch.yaml"
        mocked_func = mocker.patch("lyopronto.opt_Pch.dry", wraps=opt_Pch.dry, autospec=True)
        with chdir(tmp_path):
            inputs = read_inputs(input_file)

            save_inputs(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.yaml").exists()
            save_inputs_legacy(inputs, "testtime")
            assert (tmp_path / "lyopronto_input_testtime.csv").exists()

            output = execute_simulation(inputs)
            assert mocked_func.call_count == 1 # Should be called multiple times by rootfinder

            save_csv(output, inputs, "testtime")
            assert (tmp_path / "lyopronto_output_testtime.csv").exists()

            generate_visualizations(output, inputs, "testtime")
            assert (tmp_path / "lyo_Temperatures_testtime.pdf").exists()
            assert (tmp_path / "lyo_Pressure_SublimationFlux_testtime.pdf").exists()
            assert (tmp_path / "lyo_DryingProgress_testtime.pdf").exists()

    @pytest.mark.main
    def test_misspelled(self, repo_root):
        input_file = repo_root / "test_data" / "example_knownrp.yaml"
        inputs = read_inputs(input_file)
        inputs["sim"]["tool"] = "Primery Drying Calculator" # Misspelled on purpose
        with pytest.raises(ValueError, match="Invalid simulation tool"):
            execute_simulation(inputs)