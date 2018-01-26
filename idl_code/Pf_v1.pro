pro Pf_v1
 
  ;Malaria variable #1
  ;This is a static (one-off) product made from 2 other static products
  ;Basically the simplist-case for data production

  close, /all
  envi, /restore_base_save_files
  envi_batch_init
  
  PRINT, 'Program start time ', SYSTIME()
  
  no_data_value = -9999
    
  ; The template file  
  template_file = 'C:\MAP_other_stuff\HIV\new_tifs\african_cn1km_2013.tif' 
  ENVI_OPEN_FILE, template_file, r_fid = fid_template
  map_info_out = ENVI_GET_MAP_INFO(fid = fid_template)
  ENVI_FILE_QUERY, fid_template, NB = nb_template, NL = nl_template, NS = ns_template, dims = dims_template
  template_raster = ENVI_GET_DATA(fid = fid_template, dims = dims_template, pos=0)
  ENVI_FILE_MNG, ID = fid_template, /REMOVE
  
  ; The input files
  input_file_1 = 'F:\5km_mastergrid_aligned\LST_delta\max\annual.synoptic.mean.tif'
  input_file_2 = 'F:\5km_mastergrid_aligned\worldclim\prec57a2.tif'
  
  ; The output files
  output_filename_temp = 'F:\5km_mastergrid_aligned\Pf_cubes\V1\temp' ; type ENVI
  output_filename = 'F:\5km_mastergrid_aligned\Pf_cubes\V1\Pf.V1.0.0.tif'

  ; Open the iput files
  ENVI_OPEN_FILE, input_file_1, r_fid = fid_var_1
  var_1_raster = ENVI_GET_DATA(fid = fid_var_1, dims = dims_template, pos=0)
  ENVI_FILE_MNG, ID = fid_var_1, /REMOVE
  
  ENVI_OPEN_FILE, input_file_2, r_fid = fid_var_2
  var_2_raster = ENVI_GET_DATA(fid = fid_var_2, dims = dims_template, pos=0)
  ENVI_FILE_MNG, ID = fid_var_2, /REMOVE
  
  ; Declare the output raster
  output_raster = FLTARR(ns_template, nl_template)
    
  var_1_adjustment_factor = 0.0
  var_2_adjustment_factor = 1.0
  
  ; Value from the training dataset (to do the type 11 transform)
  ; Remember that these are calculated from Excel AFTER the adjustment factor has been applied
  ;var_1_mean = 
  ;var_1_stdev = 
  var_2_mean = 41.4835438258427
  var_2_stdev = 25.4252202525661


  For a = 0, ns_template -1 Do Begin
    For b = 0, nl_template -1 Do Begin
      If template_raster[a,b] NE no_data_value AND var_1_raster[a,b] NE no_data_value AND var_2_raster[a,b] NE no_data_value Then Begin
        output_raster[a,b] = var_1_raster[a,b]^2 * ABS(((var_2_raster[a,b] + var_2_adjustment_factor) - var_2_mean) / var_2_stdev) ; transform 7 on v1, transform 11 on v2
      EndIf Else output_raster[a,b] = no_data_value
    EndFor
  EndFor
  
  ; Fill in values  in the template missing in the output

  filled_count = 0
  unfilled_count = 0

  For a = 0, ns_template -1 Do Begin
    For b = 0, nl_template -1 Do Begin
      If template_raster[a,b] NE no_data_value AND output_raster[a,b] EQ no_data_value Then Begin
        
        n1 = output_raster[a+1,b]
        n2 = output_raster[a,b-1]
        n3 = output_raster[a-1,b]
        n4 = output_raster[a,b+1]
        n5 = output_raster[a+1,b+1]
        n6 = output_raster[a+1,b-1]
        n7 = output_raster[a-1,b+1]
        n8 = output_raster[a-1,b-1]
        
        sum = 0
        count = 0
        
        If n1 NE no_data_value Then Begin
          sum = n1
          count = 1
        EndIf
        If n2 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n2
            count = 1
          EndIf Else Begin
            sum = sum + n2
            count = count + 1
          EndElse
        EndIf
        If n3 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n3
            count = 1
          EndIf Else Begin
            sum = sum + n3
            count = count + 1
          EndElse
        EndIf
        If n4 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n4
            count = 1
          EndIf Else Begin
            sum = sum + n4
            count = count + 1
          EndElse
        EndIf
        If n5 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n5
            count = 1
          EndIf Else Begin
            sum = sum + n5
            count = count + 1
          EndElse
        EndIf
        If n6 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n6
            count = 1
          EndIf Else Begin
            sum = sum + n6
            count = count + 1
          EndElse
        EndIf
        If n7 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n7
            count = 1
          EndIf Else Begin
            sum = sum + n7
            count = count + 1
          EndElse
        EndIf
        If n8 NE no_data_value Then Begin
          If sum EQ no_data_value Then Begin
            sum = n8
            count = 1
          EndIf Else Begin
            sum = sum + n8
            count = count + 1
          EndElse
        EndIf
        
        If count NE 0 Then Begin
          output_raster[a,b] = sum/count
          filled_count = filled_count + 1
        EndIf Else Begin
          output_raster[a,b] = no_data_value ; in cases where there is no neighbor, leave as a no_data_value.  This may occur in island nations.
          unfilled_count =  unfilled_count + 1
        EndElse
      EndIf
    EndFor
  EndFor
  
  PRINT, 'Filled Gaps : ', filled_count, ' Unfilled Gaps : ', unfilled_count
  
  ; Write the output file
  PRINT, 'Writing ', output_filename, ' ', SYSTIME()
  ENVI_WRITE_ENVI_FILE, output_raster, out_name = output_filename_temp, ns=ns_template, nl=nl_template, nb=1, map_info = map_info_out
  ENVI_OPEN_FILE, (output_filename_temp), r_fid=fid_temp
  ENVI_FILE_QUERY, fid_temp, dims=dims_temp
  ENVI_OUTPUT_TO_EXTERNAL_FORMAT, fid = fid_temp, out_name = output_filename, pos=0, dims=dims_temp, /TIFF
  ENVI_FILE_MNG, ID = fid_temp, /REMOVE

  PRINT, 'Program end time ', SYSTIME()
End