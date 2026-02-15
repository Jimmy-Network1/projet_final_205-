@echo off
echo ============================================
echo DEPLOIEMENT VENTE DE VOITURES SUR RENDER
echo ============================================

echo 1. Verification des fichiers...
if not exist requirements.txt (
    echo ❌ requirements.txt manquant
    pause
    exit /b 1
)

if not exist Procfile (
    echo ❌ Procfile manquant
    pause
    exit /b 1
)

if not exist render.yaml (
    echo ❌ render.yaml manquant
    pause
    exit /b 1
)

echo 2. Initialisation Git...
if not exist .git (
    git init
    echo ✓ Git initialise
)

echo 3. Ajout des fichiers...
git add .
git commit -m "Deploiement sur Render - %date% %time%"

echo 4. Configuration du remote...
set /p GITHUB_URL=Entrez l'URL GitHub (ex: https://github.com/votreuser/vente-voitures.git): 
git remote add origin %GITHUB_URL%
git branch -M main

echo 5. Push vers GitHub...
git push -u origin main

echo.
echo ============================================
echo ✅ PROJET PRÊT POUR RENDER
echo ============================================
echo.
echo Maintenant sur Render.com :
echo 1. Allez sur https://render.com
echo 2. Cliquez sur "New +" → "Web Service"
echo 3. Connectez votre compte GitHub
echo 4. Selectionnez ce depot
echo 5. Laissez les parametres par defaut
echo 6. Cliquez sur "Create Web Service"
echo.
echo Votre site sera disponible en 5-10 minutes a :
echo https://vente-voitures.onrender.com
echo.
pause
