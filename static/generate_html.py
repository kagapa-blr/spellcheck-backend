import os


def generate_html():
    # Define the path to the assets folder
    assets_path = './assets'
    js_folder = os.path.join(assets_path, 'js')
    css_folder = os.path.join(assets_path, 'css')

    # List to store all the JS and CSS files to add to HTML
    js_files = []
    css_files = []

    # Walk through the js and css directories to collect file paths
    if os.path.exists(js_folder):
        for file_name in os.listdir(js_folder):
            if file_name.endswith('.js'):
                js_files.append(f"/static/assets/js/{file_name}")

    if os.path.exists(css_folder):
        for file_name in os.listdir(css_folder):
            if file_name.endswith('.css'):
                css_files.append(f"/static/assets/css/{file_name}")

    # Start generating the HTML content
    html_content = '''<!doctype html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>spellcheck</title>
'''

    # Add the JS files as <script> and <link rel="modulepreload">
    for js_file in js_files:
        if 'index' in js_file:
            # This is the main entry JS file
            html_content += f'    <script type="module" crossorigin src="{js_file}"></script>\n'
        else:
            # These are the preloaded modules
            html_content += f'    <link rel="modulepreload" crossorigin href="{js_file}">\n'

    # Add the CSS files as <link> tags
    for css_file in css_files:
        html_content += f'    <link rel="stylesheet" crossorigin href="{css_file}">\n'

    # Finish the rest of the HTML structure
    html_content += '''
</head>

<body>
    <div id="root"></div>
</body>

</html>
'''

    # Define the output file path
    output_file = '../templates/index.html'

    # Write the HTML content to the file
    with open(output_file, 'w') as file:
        file.write(html_content)

    print(f"{output_file} generated successfully with all JS and CSS paths.")


# Call the function to generate the HTML file
generate_html()
