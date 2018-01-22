% Splits the filename tiff image in smaller square tiff images of side
% small_side, saving them in the folder outfolder.
%
% Set enlarge to true if you want to have some partially empty slices,
% i.e., if you want to avoid losing pixels.
%
% Split images are generated left-to-right, top-to-bottom, e.g,
% 1 2 3
% 4 5 6
% 7 8 9
%
% tiff_split(filename, outfolder, small_side, enlarge)
% tiff_split('dapi_001.tif', 'output', 1024, true)
function tiff_split(filename, outfolder, small_side, enlarge)
    % Set default enlarge (false)
    if nargin < 4
        enlarge = false;
    end

    % Check that output folder exists
    if ~strcmp(outfolder(end), '/')
        outfolder = [outfolder '/'];
    end
    if ~exist(outfolder, 'dir')
        fprintf('Output folder not found, creating it at "%s".\n', outfolder);
        mkdir(outfolder);
    end

    % Get image information
    info = imfinfo(filename);
    nslices = numel(info);
    [x_big_side, y_big_side] = size(imread(filename, 1));
    fprintf('Found %d slices with %d x %d sizes.\n', ...
        nslices, x_big_side, y_big_side);

    % Check that big_side is divisible by small_side
    mx = mod(x_big_side, small_side);
    if 0 ~= mx
        if enlarge
            x_big_side = small_side * ceil(x_big_side / small_side);
        else
            disp(['The X size of the original image is not a multiple ' ...
                'of the provided small side. Part of the image will be lost.']);
        end
    end
    my = mod(y_big_side, small_side);
    if 0 ~= my
        if enlarge
            y_big_side = small_side * ceil(y_big_side / small_side);
        else
            disp(['The Y size of the original image is not a multiple ' ...
                'of the provided small side. Part of the image will be lost.']);
        end
    end
    
    if ~enlarge
        start_vol = x_big_side * y_big_side * nslices;
        lost_vx = ((mx * y_big_side) + (my * x_big_side) - (mx * my)) * nslices;
        if 0 ~= lost_vx
            fprintf(['WARNING! %d voxels (%.2f%%) will be lost. ' ...
                'Set enlarge=true to avoid this.\n'], ...
                lost_vx, lost_vx / start_vol * 100);
        end
    end

    % Identify top-left corners
    x_corner_coords = linspace(0, x_big_side, x_big_side / small_side + 1) + 1;
    x_corner_coords = x_corner_coords(1:(end-1));
    y_corner_coords = linspace(0, y_big_side, y_big_side / small_side + 1) + 1;
    y_corner_coords = y_corner_coords(1:(end-1));

    % Create empty cell that will host the subset images
    small_ims = cell(nslices, numel(x_corner_coords) * numel(y_corner_coords));

    % Check existing output files
    for image_counter = 1:(numel(x_corner_coords) * numel(y_corner_coords))
        % Prepare path
        [~, outname, ~] = fileparts(filename);
        path = [outfolder outname '.' int2str(image_counter) '.tif'];

        if exist(path, 'file')
            fprintf('Deleting already existing file "%s".\n', path);
            delete(path);
        end
    end

    % Cycle through slices
    for slice_id = 1:nslices
        fprintf('Splitting slice #%d...\n', slice_id);
        if enlarge
            im_in = imread(filename, slice_id);
            [xin, yin] = size(im_in);
            im = zeros(x_big_side, y_big_side, 'like', im_in);
            im(1:xin, 1:yin) = imread(filename, slice_id);
        else
            im = imread(filename, slice_id);
        end

        % Prepare path
        [~, outname, ~] = fileparts(filename);

        % Cycle through the corners
        image_counter = 1;
        for xcoord = x_corner_coords
            for ycoord = y_corner_coords
                path = [outfolder outname '.' int2str(image_counter) '.tif'];

                % Save subset images in the empty cell array
                %small_ims(slice_id,image_counter) = ...
                %   {im(xcoord:(xcoord+small_side-1), ...
                %   ycoord:(ycoord+small_side-1))};

                % Write image
                imwrite(im(xcoord:(xcoord+small_side-1), ...
                    ycoord:(ycoord+small_side-1)), path, 'writemode', 'append');

                % Increase image counter
                image_counter = image_counter + 1;
            end
        end
    end

end
