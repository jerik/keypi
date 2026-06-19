# Prevent pytest from importing keypi_chromehistory/__init__.py as a test module.
# The plugin requires 'keypirinha' which only exists inside Keypirinha's runtime.
collect_ignore = ["__init__.py"]
