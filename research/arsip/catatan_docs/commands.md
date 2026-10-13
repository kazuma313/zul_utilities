 # Buat structure yang proper
 mkdir -p src/zul/{commands,templates,utils}
 mkdir -p src/zul/templates/{agent,api,cli}
 mkdir -p tests
 # Buat files yang dibutuhkan
 touch src/zul/cli.py
 touch src/zul/commands/{__init__.py,build.py,init.py}
 touch src/zul/utils/{__init__.py,file_generator.py,config.py}
 touch tests/__init__.py

## Windows
:: Buat struktur folder
mkdir src\zul
mkdir src\zul\commands
mkdir src\zul\templates
mkdir src\zul\templates\agent
mkdir src\zul\templates\api
mkdir src\zul\templates\cli
mkdir src\zul\utils
mkdir tests

:: Buat file yang dibutuhkan
type nul > src\zul\cli.py
type nul > src\zul\commands\__init__.py
type nul > src\zul\commands\build.py
type nul > src\zul\commands\init.py
type nul > src\zul\utils\__init__.py
type nul > src\zul\utils\file_generator.py
type nul > src\zul\utils\config.py
type nul > tests\__init__.py