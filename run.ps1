# Define the directory structure
$structure = @{
    "advanced_image_crawler" = @(
        "src/__init__.py",
        "src/crawler.py",
        "src/image_processor.py",
        "src/config.py",
        "src/utils.py",
        "gui/__init__.py",
        "gui/crawler_gui.py",
        "logs/",
        "obtained_images/",
        "reports/",
        "requirements.txt",
        "main.py"
    )
}

# Create directories and files
foreach ($folder in $structure.Keys) {
    New-Item -ItemType Directory -Path $folder -Force
    foreach ($item in $structure[$folder]) {
        $path = Join-Path $folder $item
        if ($item.EndsWith("/")) {
            # Create directory
            New-Item -ItemType Directory -Path $path -Force
        } else {
            # Create file and add a comment header
            New-Item -ItemType File -Path $path -Force
            Add-Content -Path $path -Value "# $item"
        }
    }
}

Write-Host "Repository structure created successfully."
