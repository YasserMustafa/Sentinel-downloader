# Introduction
This tool allow you to download Sentinel 1 and Sentinel 2 images from the
[Sentinels Scientific Data Hub](https://scihub.copernicus.eu/).

# Features
* Download sentinel 1 and 2 images.
* Check the integrity of the downloaded files.
* For sentinel2 products, download specified tiles and/or bands or the entire
  product.
* For sentinel2 products, you can filter the products by the cloud cover
  percentage.
* Add a crontab entry launching `./job_linux.sh` to regularly check for new
  published products without any user interaction.

# Install
`git clone https://github.com/nicodebo/Sentinel-downloader.git`

# Getting started
* Fill in the `user` and `pw` of the confic.cfg file with your login credential
  from https://scihub.copernicus.eu/.
* Run either the main.py (`python main.py`) or the shell wrapper job_linux.sh
  (`./job_linux.sh`) to download images from an exemple request stored in
  request.csv. The request.csv comes with example requests. Erase them and fill
  the file with your own.
* For more details, please have a look at the documentation folder of this
  repository.

# TODO
* Translate the documentation into english
