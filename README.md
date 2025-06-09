# Ekosuite

Ekosuite is a simple Python application for organizing excessively large collections of Astrophotography images. Its name is inspired by [Ekos](https://github.com/KDE/kstars), an application excelling at remote controlling and automating telescope control and imaging but is also compatible with other software, such as [N.I.N.A.](https://nighttime-imaging.eu).

## Features

### Organization of Astrophotography Images

Ekosuite allows you to select folders where you keep your [FITS](https://en.wikipedia.org/wiki/FITS) and/or [XISF](https://pixinsight.com/xisf/) files. It will browse the folders you selected, as well as all their subfolders and build a SQLite database with a select set of [FITS header standard](https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf) information.

<img width="912" alt="Screenshot 2025-06-03 at 8 35 56 AM" src="https://github.com/user-attachments/assets/fd45e991-5e3c-43e0-bae0-3687ad308af4" />

### Export for easy stacking

Once you have chosen folders where you keep your photos and they have all been analyzed and organized in a database, you can select a target that you have imaged and prepare a project for software such as [PixInsight](https://pixinsight.com/). The application will create a new folder structure where images are ordered in folders: `night session -> light/flat/dark/bias`. Images will not be copied into the folder you chose but rather just referenced as alias/symlink which should help your disk space a lot when dealing with hundreds of large image files.

<img width="1443" alt="Screenshot 2025-06-03 at 9 03 08 AM" src="https://github.com/user-attachments/assets/bef6e0b2-42a3-444a-9b07-a92e2153cc2b" />

### In progress: Image Analysis

A small proof of concept exists with MPSAS (Magnitude per square arc seconds) visualization. This metric isn't necessarily something a lot of people care about or save on their images as it requires a Sky Quality Meter to be connected to the imaging software. I'm working on integrating some features of `astropy` here to do a more generic on-demand analysis of images so I can visualize the quality of image data itself.

<img width="912" alt="Screenshot 2025-06-03 at 8 36 44 AM" src="https://github.com/user-attachments/assets/c8efe0be-cdd4-472e-b80d-e5fd1656608c" />

## Build & Run

This should really be as easy as opening command line and typing `make build; make run`

### Generate MacOS app

After having built the application with `make build` you can generate a Mac application with `make macapp`

### Run tests

Unit tests exist and can be run with `make test`.

## How to

To understand how this application works, there are a few basic assumptions about how images are taken and what information they contain. A lot of this is based on standard FITS format information but still worth calling out to understand what this application does.

* Imaging targets
    * Whenever you take an image in your imaging software you choose a name for your target. This name gets saved as `OBJECT` in FITS files and this is what we use for target names. If you named a target in different ways you can just export each of those targets into separate folders and then combine those folders.
    * **TL;DR**: Consider how you name targets - try sticking to one name for the same target
* Calibration frames
    * The application assumes that you use Flat, Dark and Bias frames to calibrate your light frames. This isn't a hard requirement for creating a project folder but will show up as a warning if they are missing.
    * Before creating a project a requirement is currently that you already created master dark and master bias files to use. In the project assistant there is a button to "Add missing info for dark/bias frames", since stacked calibration frames may have lost information about which CCD temperature, Gain and Offset/Bias was used - these values should generally match the ones that were used on a light frame in order to calibrate it.
    * Dark/Bias frames are considered to be valid for a specific amount of time. In the project assistant's settings you can choose how long that time frame would be. When auto-selecting dark/bias frames, the application will choose the ones that have been taken closest to the date that a light frame was taken and matches CCD temperature, gain and offset.
    * **TL;DR**: Stack some master dark/bias frames ahead of time and keep them in a folder that you have chose in Ekosuite so that they can be used for project generation. Set their missing information where needed.
* Date & Time
    * Images are automatically ordered into night sessions based on the observation date set on FITS headers (images after noon are considered for the next night, images before noon are considered for the previous night). Since this time is generally given in GMT (N.I.N.A. saves local time separately) it is by itself not a good data point to determine what night (in your local timezone) the image was actually taken.
    * Here is what the application does to then determine local time: The location information on your image is being used to determine your local timezone at the time of taking an image. This value is then saved and used to adjust the observation time for your local time.
    * **TL;DR**: Maintain a correct system clock while imaging (Raspberry Pi without internet connection for example may need manual date/time setting here) and always maintain a roughly correct location (which may be even more important for other things, such as polar-aligning your mount etc. anyways). A connected USB GPS device can help to solve both these problems with some hacking.

## Wishlist

There are a few things I'd love to get to over time as I iterate on this program in my spare time, loosely ordered by how I prioritize them:

* Providing tools for image analysis (In Progress)
    * Analyze FWHM, SNR and Median of images
    * When preparing projects, add a filter to drop images that deviate from quality thresholds (akin to subframe selector in PixInsight)
* AstroBin integration ([auto-generate CSV data](https://welcome.astrobin.com/importing-acquisitions-from-csv) for exporting acquisition information when uploading a processed image)
* See if the program runs as expected on Windows & Linux
* Make the UI a whole lot prettier
* The UI currently doesn't reload in many places when new images were analyzed and added to the database. Restarting the application or re-opening a plugin is currently the workaround for this.
* Support dark-flat calibration frames

## Known Issues

* Qt Issue on MacOS: The application at times fails to launch with an error along the lines of `Could not load the Qt platform plugin "cocoa" in "" even though it was found.`
    * Clean & Reinstall temporarily solves this: `make clean; make install` -> then run the app again
* Excessive attempts to import files
    * Not great, but not impacting the user experience either: when the application starts a lot of newly files are scanned more than once. Likely because of the way I set up folder scanners but doesn't impact the experience or add images multiple times given that the file name is unique.
    * Either Ekos or MacOS appear to also create some hidden FITS files along the actual fits files. Thankfully those don't appear to have proper header information and aren't imported in the database:
```
Error reading FITS header: FITSIO status = 107: tried to move past end of file
ffopen could not interpret primary array header of file: 
/Volumes/Extreme SSD/Astrophotography/Ekos/2025-06-02/Flat/._Flat_10.868_secs_H_
2025-06-02T21-31-36_001.fits
```
