classdef ggBioFormats
    %GGBIOFORMATS Manages BioFormat conversions
	%	Provided the path to the directory containing the nd2 files,
	%	they will be converted to tif format. Provided the path to a
	%	nd2 file, it will be converted to tif format.
	%
	%	It requires ggBioFormats and ggStack3D from the Common project,
	%	which in turn require you to download the bfmatlab.zip folder
	%	from http://downloads.openmicroscopy.org/bio-formats/5.1.5/
	%	Then add the location of the uncompressed folder with the command
	%	addpath(genpath(location_path));
	%
    
    properties
    	version = 1;					% Class version
    end
    
	methods (Static)
		function [dirname, flist] = nd2_to_tif(source)
			%% Converts nd2 file(s) to tif.
			% Provided the path to the directory containing the nd2 files,
			% they will be converted to tif format. Provided the path to a
			% nd2 file, it will be converted to tif format.
			
			dirname = '';
			flist = [];
			msg = '';

			% When a dir path is provided
			if exist(source, 'dir')
				% Add trailing slash
				if ~(source(end) == '/')
					source = [source '/'];
				end

				dirname = source;
				flist = dir([source '*.nd2']);

			% When a file path is provided
			elseif exist(source, 'file')
				[dirname, ~, ext] = fileparts(source);
				
				% Add trailing slash
				if ~(dirname(end) == '/')
					dirname = [dirname '/'];
				end

				% Check file extension
				if strcmp(ext, '.nd2')
					flist = dir(source);
				else
					disp(msg);
				end
			else
				disp(msg);
			end
			
			% Convert files
			for file_id = 1:numel(flist)
				fname = flist(file_id).name;
				fprintf('\nConverting "%s".\n', [dirname fname])

				ggBioFormats.nd2_to_tif_single(fname, dirname);
			end
		end
		function nd2_to_tif_single(fname, dirname)
			%% Converts a single nd2 file to tif.
			
			warning('off', 'BF:lowJavaMemory');

			% Load BioFormats reader
			r = bfGetReader([dirname fname]);

			% Create output folder
			[~, name, ~] = fileparts(fname);
			outdir_base = [dirname name];
			outdir = [outdir_base '/'];
			outdir_made = false;
			outdir_suffix = 0;
			while ~outdir_made
				if ~exist(outdir, 'dir')
					if exist(outdir, 'file')
						outdir_suffix = outdir_suffix + 1;
						outdir = [outdir_base '_'...
							int2str(outdir_suffix) '/'];
					else
						mkdir(outdir)
						fprintf(' Created directory "%s".\n', outdir)
						outdir_made = true;
					end
				else
					fprintf(' Directory "%s" already exists.\n', outdir)
					outdir_made = true;
				end
			end

			fprintf('\n  Dimension order: %s\n', char(r.getDimensionOrder()));
			fprintf('  Number of series: %d\n', char(r.getSeriesCount));
			fprintf('  Shape: [%d, %d, %d]\n  Number of channels: %d\n\n', ...
				r.getSizeX(), r.getSizeY(), ...
				r.getSizeZ(), r.getSizeC());

			% Retrieve metadata
			% Metadata structure at https://goo.gl/tFEh6L
			o = r.getMetadataStore();

			% Cycle series
			for series_id = 0:(r.getSeriesCount() - 1)
				r.setSeries(series_id);

				% Cycle channels
				for channel_id = 0:(r.getSizeC() - 1)
					channel_name = char(o.getChannelName(0, channel_id));
					outname = sprintf('%s%s.channel%02d.series%03d.tif',...
						outdir, channel_name,...
						(channel_id + 1), (series_id + 1));

					if exist(outname, 'file')
						fprintf('  Channel %i%s\n',...
							channel_id + 1, ' was previously converted.');
						fprintf('  Remove the file "%s"%s\n',...
							outname, ' to convert it again.');
					else
						% Prepare empty stack
						V = zeros(r.getSizeX(), r.getSizeY(),...
							r.getSizeZ(), 1, 1, 'uint16');

						% Cycle slices
						for slice_id = 0:(r.getSizeZ() - 1)
							plane = r.getIndex(slice_id, channel_id, 0) + 1;
							plane = bfGetPlane(r, plane);
							V(:, :, slice_id + 1, 1, 1) = plane;
						end

						% Write Tiff
						fprintf('  Writing to "%s".\n', outname);
						bfsave(V, outname, 'BigTiff', true);
					end
				end
			end

			r.close();

			warning('on', 'BF:lowJavaMemory');
		end
		function [dirname, flist] = to_tif(source, ext)
			%% Converts .ext file(s) to tif.
			% Provided the path to the directory containing the .ext files,
			% they will be converted to tif format. Provided the path to a
			% .ext file, it will be converted to tif format.
			
			dirname = '';
			flist = [];
			msg = '';

			% When a dir path is provided
			if exist(source, 'dir')
				% Add trailing slash
				if ~(source(end) == '/')
					source = [source '/'];
				end

				dirname = source;
				flist = dir([source '*.' ext]);

			% When a file path is provided
			elseif exist(source, 'file')
				[dirname, ~, ext] = fileparts(source);
				
				% Add trailing slash
				if ~(dirname(end) == '/')
					dirname = [dirname '/'];
				end

				% Check file extension
				if strcmp(ext, ['.' ext])
					flist = dir(source);
				else
					disp(msg);
				end
			else
				disp(msg);
			end
			
			% Convert files
			for file_id = 1:numel(flist)
				fname = flist(file_id).name;
				fprintf('\nConverting "%s".\n', [dirname fname])

				ggBioFormats.to_tif_single(fname, dirname);
			end
		end
		function to_tif_single(fname, dirname)
			%% Converts a single .ext file to tif.
			
			warning('off', 'BF:lowJavaMemory');

			% Load BioFormats reader
			r = bfGetReader([dirname fname]);

			% Create output folder
			[~, name, ~] = fileparts(fname);
			outdir_base = [dirname name];
			outdir = [outdir_base '/'];
			outdir_made = false;
			outdir_suffix = 0;
			while ~outdir_made
				if ~exist(outdir, 'dir')
					if exist(outdir, 'file')
						outdir_suffix = outdir_suffix + 1;
						outdir = [outdir_base '_'...
							int2str(outdir_suffix) '/'];
					else
						mkdir(outdir)
						fprintf(' Created directory "%s".\n', outdir)
						outdir_made = true;
					end
				else
					fprintf(' Directory "%s" already exists.\n', outdir)
					outdir_made = true;
				end
			end

			fprintf('\n  Dimension order: %s\n', char(r.getDimensionOrder()));
			fprintf('  Number of series: %d\n', char(r.getSeriesCount));
			fprintf('  Shape: [%d, %d, %d]\n  Number of channels: %d\n\n', ...
				r.getSizeX(), r.getSizeY(), ...
				r.getSizeZ(), r.getSizeC());

			% Retrieve metadata
			% Metadata structure at https://goo.gl/tFEh6L
			o = r.getMetadataStore();

			% Cycle series
			for series_id = 0:(r.getSeriesCount() - 1)
				r.setSeries(series_id);

				% Cycle channels
				for channel_id = 0:(r.getSizeC() - 1)
					channel_name = char(o.getChannelName(0, channel_id));
					outname = sprintf('%s%s.channel%02d.series%03d.tif',...
						outdir, channel_name,...
						(channel_id + 1), (series_id + 1));

					if exist(outname, 'file')
						fprintf('  Channel %i%s\n',...
							channel_id + 1, ' was previously converted.');
						fprintf('  Remove the file "%s"%s\n',...
							outname, ' to convert it again.');
					else
						% Prepare empty stack
						V = zeros(r.getSizeX(), r.getSizeY(),...
							r.getSizeZ(), 1, 1, 'uint16');

						% Cycle slices
						for slice_id = 0:(r.getSizeZ() - 1)
							plane = r.getIndex(slice_id, channel_id, 0) + 1;
							plane = bfGetPlane(r, plane);
							V(:, :, slice_id + 1, 1, 1) = plane;
						end

						% Write Tiff
						fprintf('  Writing to "%s".\n', outname);
						bfsave(V, outname, 'BigTiff', true);
					end
				end
			end

			r.close();

			warning('on', 'BF:lowJavaMemory');
		end
	end
    
end

