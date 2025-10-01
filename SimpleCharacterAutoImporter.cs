using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections;
using UnityEditor.SceneManagement;

[InitializeOnLoad]
public class SimpleCharacterAutoImporter : AssetPostprocessor
{
    private static string configPath => Application.dataPath + "/../character_import_config.json";
    private static bool isProcessing = false;
    
    static SimpleCharacterAutoImporter()
    {
        EditorApplication.update += CheckForImportConfig;
    }
    
    static void CheckForImportConfig()
    {
        if (!isProcessing && File.Exists(configPath))
        {
            Debug.Log("[AUTO-IMPORTER] Config detected - Starting import process");
            isProcessing = true;
            EditorApplication.delayCall += ProcessImportConfig;
        }
    }
    
    static void ProcessImportConfig()
    {
        try
        {
            if (!File.Exists(configPath))
            {
                Debug.LogError("Config file not found: " + configPath);
                isProcessing = false;
                return;
            }
            
            string jsonContent = File.ReadAllText(configPath);
            var config = JsonUtility.FromJson<ImportConfig>(jsonContent);
            
            Debug.Log("[AUTO-IMPORTER] Processing character: " + config.fbx_relative_path);
            
            // Delete config file immediately
            File.Delete(configPath);
            Debug.Log("[AUTO-IMPORTER] Config file deleted");
            
            // Start the import process
            EditorApplication.delayCall += () => StartCharacterImport(config);
        }
        catch (System.Exception e)
        {
            Debug.LogError("Error in SimpleCharacterAutoImporter: " + e.Message);
            isProcessing = false;
        }
    }
    
    static void StartCharacterImport(ImportConfig config)
    {
        EditorApplication.update += ImportUpdate;
        EditorCoroutine.Start(ImportCharacterCoroutine(config));
    }
    
    static void ImportUpdate()
    {
        // Empty update method for the coroutine
    }
    
    static IEnumerator ImportCharacterCoroutine(ImportConfig config)
    {
        Debug.Log("[AUTO-IMPORTER] Step 1: Importing FBX file...");
        
        // Force import the FBX
        AssetDatabase.ImportAsset(config.fbx_relative_path, ImportAssetOptions.ForceUpdate);
        yield return null;
        
        // Wait for import to complete
        while (AssetDatabase.IsAssetImportWorkerProcess())
        {
            yield return null;
        }
        
        Debug.Log("[AUTO-IMPORTER] Step 2: Configuring Humanoid rig...");
        
        // Configure the model importer for Humanoid
        ModelImporter modelImporter = AssetImporter.GetAtPath(config.fbx_relative_path) as ModelImporter;
        if (modelImporter != null)
        {
            modelImporter.animationType = ModelImporterAnimationType.Human;
            modelImporter.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            modelImporter.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            modelImporter.materialLocation = ModelImporterMaterialLocation.External;
            
            // Set scale to fix large character issue
            modelImporter.useFileScale = false;
            modelImporter.globalScale = 0.01f;
            modelImporter.useFileUnits = false;
            
            modelImporter.SaveAndReimport();
            Debug.Log("[AUTO-IMPORTER] ✓ Configured as Humanoid with scale 0.01");
        }
        
        yield return null;
        
        Debug.Log("[AUTO-IMPORTER] Step 3: Extracting materials to Textures folder...");
        ExtractMaterialsToFolder(config.fbx_relative_path);
        yield return null;
        
        Debug.Log("[AUTO-IMPORTER] Step 4: Adding character to scene...");
        AddCharacterToScene(config.fbx_relative_path);
        
        Debug.Log("[AUTO-IMPORTER] ✓ ALL STEPS COMPLETED - Character is ready for Play mode!");
        isProcessing = false;
        EditorApplication.update -= ImportUpdate;
    }
    
    static void ExtractMaterialsToFolder(string fbxPath)
    {
        // Create Textures folder if it doesn't exist
        string texturesFolder = "Assets/Textures";
        if (!AssetDatabase.IsValidFolder(texturesFolder))
        {
            AssetDatabase.CreateFolder("Assets", "Textures");
        }
        
        // Extract all materials and textures
        Object[] assets = AssetDatabase.LoadAllAssetsAtPath(fbxPath);
        foreach (Object asset in assets)
        {
            if (asset is Material material)
            {
                string materialPath = Path.Combine(texturesFolder, material.name + ".mat");
                
                if (!AssetDatabase.LoadAssetAtPath<Material>(materialPath))
                {
                    Material newMaterial = new Material(material);
                    AssetDatabase.CreateAsset(newMaterial, materialPath);
                    Debug.Log("[AUTO-IMPORTER] ✓ Extracted material: " + material.name);
                }
            }
        }
        
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
    }
    
    static void AddCharacterToScene(string fbxPath)
    {
        // Load the character prefab
        GameObject characterPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (characterPrefab == null)
        {
            Debug.LogError("[AUTO-IMPORTER] Failed to load character prefab: " + fbxPath);
            return;
        }
        
        // Find or create PlayerArmature
        GameObject playerArmature = GameObject.Find("PlayerArmature");
        if (playerArmature == null)
        {
            playerArmature = new GameObject("PlayerArmature");
            Debug.Log("[AUTO-IMPORTER] Created new PlayerArmature");
        }
        
        // Find or create Geometry under PlayerArmature
        Transform geometry = playerArmature.transform.Find("Geometry");
        if (geometry == null)
        {
            GameObject geometryObj = new GameObject("Geometry");
            geometryObj.transform.SetParent(playerArmature.transform);
            geometryObj.transform.localPosition = Vector3.zero;
            geometryObj.transform.localRotation = Quaternion.identity;
            geometryObj.transform.localScale = Vector3.one;
            geometry = geometryObj.transform;
            Debug.Log("[AUTO-IMPORTER] Created Geometry folder");
        }
        
        // Clear existing geometry children
        foreach (Transform child in geometry)
        {
            UnityEngine.Object.DestroyImmediate(child.gameObject);
        }
        
        // Instantiate the character under Geometry
        GameObject characterInstance = PrefabUtility.InstantiatePrefab(characterPrefab) as GameObject;
        characterInstance.transform.SetParent(geometry);
        characterInstance.transform.localPosition = Vector3.zero;
        characterInstance.transform.localRotation = Quaternion.identity;
        characterInstance.transform.localScale = Vector3.one;
        
        Debug.Log("[AUTO-IMPORTER] ✓ Added character to PlayerArmature/Geometry");
        
        // Update Animator avatar
        UpdateAnimatorAvatar(playerArmature, characterInstance);
        
        // Select the PlayerArmature in hierarchy
        Selection.activeGameObject = playerArmature;
        SceneView.FrameLastActiveSceneView();
        
        // Save scene
        if (EditorSceneManager.GetActiveScene().isDirty)
        {
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
            Debug.Log("[AUTO-IMPORTER] ✓ Scene saved");
        }
    }
    
    static void UpdateAnimatorAvatar(GameObject playerArmature, GameObject characterInstance)
    {
        // Get or add Animator to PlayerArmature
        Animator playerAnimator = playerArmature.GetComponent<Animator>();
        if (playerAnimator == null)
        {
            playerAnimator = playerArmature.AddComponent<Animator>();
        }
        
        // Get avatar from character
        Animator characterAnimator = characterInstance.GetComponent<Animator>();
        if (characterAnimator != null && characterAnimator.avatar != null)
        {
            playerAnimator.avatar = characterAnimator.avatar;
            Debug.Log("[AUTO-IMPORTER] ✓ Updated Animator avatar");
        }
        else
        {
            Debug.LogWarning("[AUTO-IMPORTER] No avatar found on character - may need manual setup");
        }
        
        // Remove animator from character instance (should be on PlayerArmature only)
        Animator charInstanceAnimator = characterInstance.GetComponent<Animator>();
        if (charInstanceAnimator != null)
        {
            UnityEngine.Object.DestroyImmediate(charInstanceAnimator);
        }
    }
    
    [System.Serializable]
    public class ImportConfig
    {
        public string fbx_relative_path;
        public string character_name;
    }
    
    // Simple coroutine implementation without duplicate class issues
    public static class EditorCoroutine
    {
        private static System.Collections.IEnumerator currentRoutine;
        
        public static void Start(System.Collections.IEnumerator routine)
        {
            currentRoutine = routine;
            EditorApplication.update += Update;
        }
        
        private static void Update()
        {
            if (currentRoutine != null)
            {
                if (!currentRoutine.MoveNext())
                {
                    currentRoutine = null;
                    EditorApplication.update -= Update;
                }
            }
        }
    }
}