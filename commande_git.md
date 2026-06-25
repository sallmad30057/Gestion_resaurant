# Commandes Git

1. Se positionner sur main
git checkout main

2. Récupérer le fichier depuis la branche coding
git checkout coding -- NomDuFichier.py

3. Ajouter le fichier à l'index
git add NomDuFichier.py

4. Committer le fichier sur main
git commit -m "Ajout du fichier NomDuFichier.py depuis coding"

5. Pousser sur main
git push origin main

6. Retourner sur coding pour continuer travailler
git checkout coding