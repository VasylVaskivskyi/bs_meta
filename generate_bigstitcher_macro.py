from pathlib import Path
from datetime import datetime


class BigStitcherMacro:
    def __init__(self):
        self.img_dir = Path
        self.out_dir = Path
        self.xml_file_name = 'dataset.xml'
        self.pattern = '1_{xxxxx}_Z001.tif'

        # range: 1-5 or list: 1,2,3,4,5
        self.num_tiles = 1

        self.num_tiles_x = 1
        self.num_tiles_y = 1

        # overlap in percent
        self.overlap_x = 10
        self.overlap_y = 10
        self.overlap_z = 1

        # distance in um
        self.pixel_distance_x = 1
        self.pixel_distance_y = 1
        self.pixel_distance_z = 1

        self.tiling_mode = ''
        self.region = 1

        self.__location = Path(__file__).parent.resolve()


    def generate(self):
        formatted_macro = self.replace_values_in_macro()
        macro_file_path = self.write_to_temp_macro_file(formatted_macro)
        return macro_file_path


    def convert_tiling_mode(self, tiling_mode):
        if tiling_mode == 'snake':
            bigstitcher_tiling_mode = '[Snake: Right & Down      ]'
        elif tiling_mode == 'grid':
            bigstitcher_tiling_mode = '[Grid: Right & Down      ]'
        return bigstitcher_tiling_mode


    def replace_values_in_macro(self):
        macro_template = self.estimate_stitch_param_macro_template
        formatted_macro = macro_template.format(img_dir=self.path_to_str(self.img_dir),
                                                out_dir=self.path_to_str(self.out_dir),
                                                path_to_xml_file=self.path_to_str(self.img_dir.joinpath(self.xml_file_name)),
                                                pattern=self.pattern,
                                                num_tiles=self.make_range(self.num_tiles),
                                                num_tiles_x=self.num_tiles_x,
                                                num_tiles_y=self.num_tiles_y,
                                                overlap_x=self.overlap_x,
                                                overlap_y=self.overlap_y,
                                                overlap_z=self.overlap_z,
                                                pixel_distance_x=self.pixel_distance_x,
                                                pixel_distance_y=self.pixel_distance_y,
                                                pixel_distance_z=self.pixel_distance_z,
                                                tiling_mode=self.convert_tiling_mode(self.tiling_mode)
                                                )
        return formatted_macro


    def write_to_temp_macro_file(self, formatted_macro):
        file_name = 'reg' + str(self.region) + '_bigstitcher_macro.ijm'
        macro_file_path = self.out_dir.joinpath(file_name)
        with open(macro_file_path, 'w') as f:
            f.write(formatted_macro)
        return macro_file_path

    def make_range(self, number):
        return ','.join([str(n) for n in range(1, number+1)])

    def path_to_str(self, path: Path):
        return str(path.absolute().as_posix())

    estimate_stitch_param_macro_template = """
    // define dataset
    run("BigStitcher",
        "select=define" +
        " define_dataset=[Manual Loader (Bioformats based)]" +
        " project_filename={path_to_xml_file}" +
        " multiple_timepoints=[NO (one time-point)]" +
        " multiple_channels=[NO (one channel)]" +
        " _____multiple_illumination_directions=[NO (one illumination direction)]" +
        " multiple_angles=[NO (one angle)]" +
        " multiple_tiles=[YES (one file per tile)]" +
        " image_file_directory={img_dir}" +
        " image_file_pattern={pattern}" +
        " timepoints_=1" +
        " tiles_={num_tiles}" +
        " move_tiles_to_grid_(per_angle)?=[Move Tile to Grid (Macro-scriptable)]" +
        " grid_type={tiling_mode}" +
        " tiles_x={num_tiles_x}" +
        " tiles_y={num_tiles_y}" +
        " tiles_z=1" +
        " overlap_x_(%)={overlap_x}" +
        " overlap_y_(%)={overlap_y}" +
        " overlap_z_(%)={overlap_z}" +
        " calibration_type=[Same voxel-size for all views]" +
        " calibration_definition=[User define voxel-size(s)]" +
        " imglib2_data_container=[ArrayImg (faster)]" +
        " pixel_distance_x={pixel_distance_x}" +
        " pixel_distance_y={pixel_distance_y}" +
        " pixel_distance_z={pixel_distance_z}" +
        " pixel_unit=um");

    // calculate pairwise shifts
    run("Calculate pairwise shifts ...",
        "select={path_to_xml_file}" +
        " process_angle=[All angles]" +
        " process_channel=[All channels]" +
        " process_illumination=[All illuminations]" +
        " process_tile=[All tiles]" +
        " process_timepoint=[All Timepoints]" +
        " method=[Phase Correlation]" +
        " show_expert_algorithm_parameters" +
        " downsample_in_x=1" +
        " downsample_in_y=1" +
        " number=5" +
        " minimal=10" +
        " subpixel");

    // filter shifts with 0.7 corr. threshold
    run("Filter pairwise shifts ...",
        "select={path_to_xml_file}" +
        " filter_by_link_quality" +
        " min_r=0.7" +
        " max_r=1" +
        " max_shift_in_x=0" +
        " max_shift_in_y=0" +
        " max_shift_in_z=0" +
        " max_displacement=0");

    // do global optimization
    run("Optimize globally and apply shifts ...",
        "select={path_to_xml_file}" +
        " process_angle=[All angles]" +
        " process_channel=[All channels]" +
        " process_illumination=[All illuminations]" +
        " process_tile=[All tiles]" +
        " process_timepoint=[All Timepoints]" +
        " relative=2.500" +
        " absolute=3.500" +
        " global_optimization_strategy=[Two-Round using Metadata to align unconnected Tiles]" +
        " fix_group_0-0,");


    // quit after we are finished
    run("Quit");
    eval("script", "System.exit(0);");

    """


class FuseMacro:
    def __init__(self):
        self.img_dir = Path('.')
        self.xml_file_name = 'dataset.xml'
        self.out_dir = Path('.')
        self.__location = Path(__file__).parent.absolute()

    def generate(self):
        formatted_macro = self.replace_values_in_macro()
        macro_file_path = self.write_to_macro_file_in_channel_dir(self.img_dir, formatted_macro)


    def replace_values_in_macro(self):
        macro_template = self.fuse_macro_template
        formatted_macro = macro_template.format(img_dir=self.path_to_str(self.img_dir),
                                                path_to_xml_file=self.path_to_str(self.img_dir.joinpath(self.xml_file_name)),
                                                out_dir=self.path_to_str(self.out_dir)
                                                )
        return formatted_macro


    def write_to_macro_file_in_channel_dir(self, img_dir: str, formatted_macro: str):
        macro_file_path = img_dir.joinpath('fuse_only_macro.ijm')
        with open(macro_file_path, 'w') as f:
            f.write(formatted_macro)
        return macro_file_path

    def path_to_str(self, path: Path):
        return str(path.absolute().as_posix())

    fuse_macro_template = """
    // fuse dataset, save as TIFF
    run("Fuse dataset ...",
        "select={path_to_xml_file}" +
        " process_angle=[All angles]" +
        " process_channel=[All channels]" +
        " process_illumination=[All illuminations]" +
        " process_tile=[All tiles]" +
        " process_timepoint=[All Timepoints]" +
        " bounding_box=[All Views]" +
        " downsampling=1" +
        " pixel_type=[16-bit unsigned integer]" +
        " interpolation=[Linear Interpolation]" +
        " image=[Precompute Image]" +
        " interest_points_for_non_rigid=[-= Disable Non-Rigid =-]" +
        " blend produce=[Each timepoint & channel]" +
        " fused_image=[Save as (compressed) TIFF stacks]" +
        " output_file_directory={out_dir}");

    """
