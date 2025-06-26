using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.swpublished;

namespace MCP.SolidWorks.Adapters
{
    /// <summary>
    /// SolidWorks 2024 specific adapter implementation
    /// </summary>
    public class SolidWorksAdapter2024 : ISolidWorksAdapter
    {
        private ISldWorks swApp;
        private IModelDoc2 activeDoc;
        private bool isConnected;

        public string Version => "2024";

        public async Task<bool> ConnectAsync()
        {
            return await Task.Run(() =>
            {
                try
                {
                    // Try to get running instance first
                    swApp = (ISldWorks)Marshal.GetActiveObject("SldWorks.Application.32");
                    
                    if (swApp == null)
                    {
                        // Create new instance if none running
                        Type swType = Type.GetTypeFromProgID("SldWorks.Application.32");
                        swApp = (ISldWorks)Activator.CreateInstance(swType);
                        swApp.Visible = true;
                    }

                    isConnected = true;
                    return true;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Failed to connect to SolidWorks: {ex.Message}");
                    return false;
                }
            });
        }

        public async Task DisconnectAsync()
        {
            await Task.Run(() =>
            {
                if (swApp != null)
                {
                    Marshal.ReleaseComObject(swApp);
                    swApp = null;
                }
                isConnected = false;
            });
        }

        public async Task<Dictionary<string, object>> OpenDocumentAsync(string filePath)
        {
            return await Task.Run(() =>
            {
                var result = new Dictionary<string, object>();
                
                try
                {
                    int errors = 0;
                    int warnings = 0;
                    
                    // Determine document type
                    string extension = System.IO.Path.GetExtension(filePath).ToLower();
                    swDocumentTypes_e docType = swDocumentTypes_e.swDocNONE;
                    
                    switch (extension)
                    {
                        case ".sldprt":
                            docType = swDocumentTypes_e.swDocPART;
                            break;
                        case ".sldasm":
                            docType = swDocumentTypes_e.swDocASSEMBLY;
                            break;
                        case ".slddrw":
                            docType = swDocumentTypes_e.swDocDRAWING;
                            break;
                    }
                    
                    activeDoc = swApp.OpenDoc6(filePath, (int)docType, 
                        (int)swOpenDocOptions_e.swOpenDocOptions_Silent, 
                        "", ref errors, ref warnings);
                    
                    result["success"] = activeDoc != null;
                    result["errors"] = errors;
                    result["warnings"] = warnings;
                    result["documentType"] = docType.ToString();
                    
                    if (activeDoc != null)
                    {
                        result["title"] = activeDoc.GetTitle();
                        result["path"] = activeDoc.GetPathName();
                    }
                }
                catch (Exception ex)
                {
                    result["success"] = false;
                    result["error"] = ex.Message;
                }
                
                return result;
            });
        }

        public async Task<List<Dictionary<string, object>>> GetFeaturesAsync()
        {
            return await Task.Run(() =>
            {
                var features = new List<Dictionary<string, object>>();
                
                if (activeDoc == null) return features;
                
                IFeature feat = activeDoc.FirstFeature();
                
                while (feat != null)
                {
                    var featureInfo = new Dictionary<string, object>
                    {
                        ["name"] = feat.Name,
                        ["type"] = feat.GetTypeName2(),
                        ["id"] = feat.GetID(),
                        ["suppressed"] = feat.IsSuppressed(),
                        ["dimensions"] = GetFeatureDimensions(feat)
                    };
                    
                    features.Add(featureInfo);
                    feat = feat.GetNextFeature();
                }
                
                return features;
            });
        }

        public async Task<bool> ModifyDimensionAsync(string featureName, string dimensionName, double value)
        {
            return await Task.Run(() =>
            {
                if (activeDoc == null) return false;
                
                try
                {
                    IFeature feature = activeDoc.FeatureByName(featureName);
                    if (feature == null) return false;
                    
                    IDisplayDimension dispDim = feature.GetFirstDisplayDimension();
                    
                    while (dispDim != null)
                    {
                        IDimension dim = dispDim.GetDimension();
                        
                        if (dim.Name == dimensionName || dim.FullName == dimensionName)
                        {
                            dim.SystemValue = value;
                            activeDoc.EditRebuild3();
                            return true;
                        }
                        
                        dispDim = feature.GetNextDisplayDimension(dispDim);
                    }
                    
                    return false;
                }
                catch
                {
                    return false;
                }
            });
        }

        public async Task<Dictionary<string, object>> RunMacroAsync(string macroPath, string macroName, Dictionary<string, object> parameters)
        {
            return await Task.Run(() =>
            {
                var result = new Dictionary<string, object>();
                
                try
                {
                    string moduleName = string.IsNullOrEmpty(macroName) ? "main" : macroName;
                    string procedureName = "main";
                    
                    if (macroName != null && macroName.Contains("."))
                    {
                        var parts = macroName.Split('.');
                        moduleName = parts[0];
                        procedureName = parts[1];
                    }
                    
                    bool success = swApp.RunMacro2(macroPath, moduleName, procedureName, 
                        (int)swRunMacroOption_e.swRunMacroUnloadAfterRun, 
                        out int error);
                    
                    result["success"] = success;
                    result["error"] = error;
                    result["errorMessage"] = GetMacroErrorMessage(error);
                }
                catch (Exception ex)
                {
                    result["success"] = false;
                    result["error"] = ex.Message;
                }
                
                return result;
            });
        }

        public async Task<bool> UpdateDesignTableAsync(string tableName, string configuration, Dictionary<string, object> values)
        {
            return await Task.Run(() =>
            {
                if (activeDoc == null) return false;
                
                try
                {
                    IDesignTable designTable = activeDoc.GetDesignTable();
                    if (designTable == null) return false;
                    
                    // Edit design table
                    designTable.Attach();
                    
                    // Update values in the design table
                    // This would require Excel interop or similar to modify the embedded Excel sheet
                    // For now, we'll use the configuration-specific property approach
                    
                    IConfiguration config = activeDoc.GetConfigurationByName(configuration);
                    if (config == null) config = activeDoc.GetActiveConfiguration();
                    
                    foreach (var kvp in values)
                    {
                        config.CustomPropertyManager.Add3(kvp.Key, 
                            (int)swCustomInfoType_e.swCustomInfoText, 
                            kvp.Value.ToString(), 
                            (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);
                    }
                    
                    designTable.UpdateModel((int)swDesignTableUpdateOptions_e.swUpdateDesignTableAll);
                    designTable.Detach();
                    
                    activeDoc.EditRebuild3();
                    return true;
                }
                catch
                {
                    return false;
                }
            });
        }

        public async Task<bool> ExportFileAsync(string outputPath, string format, Dictionary<string, object> options)
        {
            return await Task.Run(() =>
            {
                if (activeDoc == null) return false;
                
                try
                {
                    bool success = false;
                    
                    switch (format.ToUpper())
                    {
                        case "STEP":
                            success = activeDoc.SaveAs3(outputPath, 
                                (int)swSaveAsVersion_e.swSaveAsCurrentVersion, 
                                (int)swSaveAsOptions_e.swSaveAsOptions_Silent);
                            break;
                            
                        case "STL":
                            success = activeDoc.SaveAs3(outputPath, 
                                (int)swSaveAsVersion_e.swSaveAsCurrentVersion, 
                                (int)swSaveAsOptions_e.swSaveAsOptions_Silent);
                            break;
                            
                        case "PDF":
                            IExportPdfData pdfData = swApp.GetExportFileData(
                                (int)swExportDataFileType_e.swExportPdfData) as IExportPdfData;
                            success = activeDoc.SaveAs3(outputPath, 
                                (int)swSaveAsVersion_e.swSaveAsCurrentVersion, 
                                (int)swSaveAsOptions_e.swSaveAsOptions_Silent);
                            break;
                            
                        default:
                            success = activeDoc.SaveAs3(outputPath, 
                                (int)swSaveAsVersion_e.swSaveAsCurrentVersion, 
                                (int)swSaveAsOptions_e.swSaveAsOptions_Silent);
                            break;
                    }
                    
                    return success;
                }
                catch
                {
                    return false;
                }
            });
        }

        public async Task<Dictionary<string, object>> GetModelInfoAsync()
        {
            return await Task.Run(() =>
            {
                var info = new Dictionary<string, object>();
                
                if (activeDoc == null) return info;
                
                info["title"] = activeDoc.GetTitle();
                info["path"] = activeDoc.GetPathName();
                info["type"] = activeDoc.GetType();
                info["activeConfigurationName"] = activeDoc.IGetActiveConfiguration().Name;
                info["materialIdName"] = activeDoc.GetMaterialIdName();
                info["isModified"] = !activeDoc.GetSaveFlag();
                
                // Get custom properties
                var customProps = new Dictionary<string, string>();
                ICustomPropertyManager propMgr = activeDoc.Extension.CustomPropertyManager[""];
                string[] propNames = propMgr.GetNames() as string[];
                
                if (propNames != null)
                {
                    foreach (string propName in propNames)
                    {
                        string value, resolvedValue;
                        propMgr.Get4(propName, false, out value, out resolvedValue);
                        customProps[propName] = resolvedValue;
                    }
                }
                
                info["customProperties"] = customProps;
                
                // Get mass properties if it's a part or assembly
                if (activeDoc.GetType() != (int)swDocumentTypes_e.swDocDRAWING)
                {
                    IMassProperty massProp = activeDoc.Extension.CreateMassProperty();
                    info["mass"] = massProp.Mass;
                    info["volume"] = massProp.Volume;
                    info["surfaceArea"] = massProp.SurfaceArea;
                    info["centerOfMass"] = new double[] { massProp.CenterOfMass[0], 
                                                          massProp.CenterOfMass[1], 
                                                          massProp.CenterOfMass[2] };
                }
                
                return info;
            });
        }

        public async Task<Tuple<bool, List<string>>> RebuildModelAsync(bool force)
        {
            return await Task.Run(() =>
            {
                var errors = new List<string>();
                
                if (activeDoc == null)
                {
                    errors.Add("No active document");
                    return new Tuple<bool, List<string>>(false, errors);
                }
                
                try
                {
                    bool success = false;
                    
                    if (force)
                    {
                        success = activeDoc.ForceRebuild3(false);
                    }
                    else
                    {
                        success = activeDoc.EditRebuild3();
                    }
                    
                    // Check for rebuild errors
                    IFeature feat = activeDoc.FirstFeature();
                    while (feat != null)
                    {
                        if (feat.GetErrorCode() != 0)
                        {
                            errors.Add($"Feature '{feat.Name}' has error: {feat.GetErrorCode()}");
                        }
                        feat = feat.GetNextFeature();
                    }
                    
                    return new Tuple<bool, List<string>>(success && errors.Count == 0, errors);
                }
                catch (Exception ex)
                {
                    errors.Add(ex.Message);
                    return new Tuple<bool, List<string>>(false, errors);
                }
            });
        }

        // Helper methods
        private List<Dictionary<string, object>> GetFeatureDimensions(IFeature feature)
        {
            var dimensions = new List<Dictionary<string, object>>();
            
            IDisplayDimension dispDim = feature.GetFirstDisplayDimension();
            
            while (dispDim != null)
            {
                IDimension dim = dispDim.GetDimension();
                
                var dimInfo = new Dictionary<string, object>
                {
                    ["name"] = dim.Name,
                    ["fullName"] = dim.FullName,
                    ["value"] = dim.SystemValue,
                    ["tolerance"] = dim.Tolerance.GetMinValue() + " - " + dim.Tolerance.GetMaxValue()
                };
                
                dimensions.Add(dimInfo);
                dispDim = feature.GetNextDisplayDimension(dispDim);
            }
            
            return dimensions;
        }

        private string GetMacroErrorMessage(int errorCode)
        {
            switch (errorCode)
            {
                case 0: return "Success";
                case 1: return "File not found";
                case 2: return "Failed to run macro";
                case 3: return "Macro contains syntax errors";
                case 4: return "Macro was cancelled by user";
                default: return $"Unknown error code: {errorCode}";
            }
        }
    }

    public interface ISolidWorksAdapter
    {
        string Version { get; }
        Task<bool> ConnectAsync();
        Task DisconnectAsync();
        Task<Dictionary<string, object>> OpenDocumentAsync(string filePath);
        Task<List<Dictionary<string, object>>> GetFeaturesAsync();
        Task<bool> ModifyDimensionAsync(string featureName, string dimensionName, double value);
        Task<Dictionary<string, object>> RunMacroAsync(string macroPath, string macroName, Dictionary<string, object> parameters);
        Task<bool> UpdateDesignTableAsync(string tableName, string configuration, Dictionary<string, object> values);
        Task<bool> ExportFileAsync(string outputPath, string format, Dictionary<string, object> options);
        Task<Dictionary<string, object>> GetModelInfoAsync();
        Task<Tuple<bool, List<string>>> RebuildModelAsync(bool force);
    }
}