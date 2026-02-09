import sys
print(f"🔍 Je tourne avec ce Python : {sys.executable}")

print("--- TENTATIVE D'IMPORT ---")
try:
    import os
    # On calme les logs de TensorFlow pour y voir clair
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
    
    import tensorflow as tf
    print(f"✅ TensorFlow version : {tf.__version__}")
    
    from deepface import DeepFace
    print("✅ SUCCÈS TOTAL : DeepFace est installé et fonctionne !")
    
except ImportError as e:
    print(f"❌ ERREUR D'IMPORTATION : {e}")
    print("C'est souvent parce que la librairie n'est pas trouvée.")

except Exception as e:
    print(f"❌ ERREUR AU CHARGEMENT : {e}")
    print("Ça, c'est une erreur technique (DLL manquante, conflit de version...)")