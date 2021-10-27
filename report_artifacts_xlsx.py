'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Oct 27 2021
File : report_artifacts_xlsx.py
'''

import logging
import xlsxwriter

import _version

logger = logging.getLogger(__name__)

# Colors for report
reveneraGray = '#323E48'
white = '#FFFFFF'
p1LicenseColor = "#C00000"
p2LicenseColor = "#FFFF00"
p3LicenseColor= "#008000"
NALicenseColor = "#D3D3D3"
criticalVulnColor = "#400000"
highVulnColor = "#C00000"
mediumVulnColor = "#FFA500"
lowVulnColor = "#FFFF00"
noneVulnColor = "#D3D3D3"
approvedColor = "#008000"
rejectedColor = "#C00000"
draftColor = "#D3D3D3"


#------------------------------------------------------------------#
def generate_xlsx_report(reportData):
    logger.info("    Entering generate_xlsx_report")
    reportName = reportData["reportName"]
    projectName = reportData["projectName"]
    projectNameForFile  = reportData["projectNameForFile"] 
    projectID = reportData["projectID"] 
    fileNameTimeStamp = reportData["fileNameTimeStamp"] 
    inventoryData = reportData["inventoryData"]
    projectList = reportData["projectList"]
    reportOptions = reportData["reportOptions"]
    projectHierarchy = reportData["projectHierarchy"]


    if len(projectList)==1:
        xlsxFile = projectNameForFile + "-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx"
    else:
        xlsxFile = projectNameForFile + "-with-children-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx" 

    # Create the workbook/worksheet for storying the data
    workbook = xlsxwriter.Workbook(xlsxFile)

    tableHeaderFormat = workbook.add_format()
    tableHeaderFormat.set_text_wrap()
    tableHeaderFormat.set_bold()
    tableHeaderFormat.set_bg_color(reveneraGray)
    tableHeaderFormat.set_font_color(white)
    tableHeaderFormat.set_font_size('12')
    tableHeaderFormat.set_align('center')
    tableHeaderFormat.set_align('vcenter')

    cellFormat = workbook.add_format()
    cellFormat.set_text_wrap()
    cellFormat.set_align('center')
    cellFormat.set_align('vcenter')
    cellFormat.set_font_size('10')
    cellFormat.set_border()

    cellLinkFormat = workbook.add_format()
    cellLinkFormat.set_text_wrap()
    cellLinkFormat.set_font_size('10')
    cellLinkFormat.set_align('center')
    cellLinkFormat.set_align('vcenter')
    cellLinkFormat.set_font_color('blue')
    cellLinkFormat.set_underline()
    cellLinkFormat.set_border()

    boldCellFormat = workbook.add_format()
    boldCellFormat.set_align('vcenter')
    boldCellFormat.set_font_size('12')
    boldCellFormat.set_bold()
   

    ###############################################################################################
    # Do we need a hierarchy chart?
    if len(projectList) > 1:

        hierachyWorksheet = workbook.add_worksheet('Project Hierarchy')
        hierachyWorksheet.hide_gridlines(2)
        hierachyWorksheet.write('B2', projectName, boldCellFormat) # Row 2, column 1
        row=1
        column=1
        display_project_hierarchy(hierachyWorksheet, projectHierarchy, row, column, boldCellFormat)

    ############################################################
    # Fill out the SBOM details worksheet
    detailsWorksheet = workbook.add_worksheet('SBOM') 

    column=0
    row=0
    
    # Set the default column widths
    tableHeaders = []

    if len(projectList) > 1:
        detailsWorksheet.set_column(column, column, 25)
        tableHeaders.append("PROJECT NAME")
        column+=1    

    detailsWorksheet.set_column(column, column, 40)
    tableHeaders.append("COMPONENT")
    column+=1

    detailsWorksheet.set_column(column, column, 15) 
    tableHeaders.append("VERSION")
    column+=1

    detailsWorksheet.set_column(column, column, 25) 
    tableHeaders.append("LICENSE")
    column+=1
    
    detailsWorksheet.set_column(column, column, 25) 
    tableHeaders.append("VULNERABILITIES")
    column+=1
    
    # Write out the column headers
    detailsWorksheet.write_row(row, 0, tableHeaders, tableHeaderFormat)

    ######################################################
    # Cycle through the inventory to create the table with the SBOM Details
    for inventoryID in sorted(inventoryData):
        row+=1
        logger.debug("        Reporting for inventory item %s" %inventoryID)

        projectName = inventoryData[inventoryID]["projectName"]
        inventoryItemName = inventoryData[inventoryID]["inventoryItemName"]
        componentName = inventoryData[inventoryID]["componentName"]
        componentVersionName = inventoryData[inventoryID]["componentVersionName"]
        selectedLicenseName = inventoryData[inventoryID]["selectedLicenseName"]
        projectLink = inventoryData[inventoryID]["projectLink"]
        hasVulnerabilities = inventoryData[inventoryID]["hasVulnerabilities"]

        logger.debug("            Project Name:  %s --> Inventory Item %s" %(projectName, inventoryItemName))

        # Now write each cell
        column=0
        
        if len(projectList) > 1:
            detailsWorksheet.write_url(row, column, projectLink, cellLinkFormat, string=projectName)
            column+=1
        
        detailsWorksheet.write(row, column, componentName, cellFormat)
        column+=1
        detailsWorksheet.write(row, column, componentVersionName, cellFormat)
        column+=1
        detailsWorksheet.write(row, column, selectedLicenseName, cellFormat)
        column+=1

        if reportOptions["includeVulnerabilities"]:
            if hasVulnerabilities:
                detailsWorksheet.write(row, column, "True", cellFormat)
            else:
                detailsWorksheet.write(row, column, "", cellFormat)


    # Automatically create the filter sort options
    detailsWorksheet.autofilter(0,0, 0 + len(inventoryData)-1, len(tableHeaders)-1)

    workbook.close()
    
    logger.info("    Exiting generate_xlsx_report")
    return xlsxFile



#------------------------------------------------------------#
def display_project_hierarchy(worksheet, parentProject, row, column, boldCellFormat):

    column +=1 #  We are level down so we need to indent
    row +=1
    # Are there more child projects for this project?

    if len(parentProject["childProject"]):
        for childProject in parentProject["childProject"]:
            projectName = childProject["name"]
            # Add this ID to the list of projects with other child projects
            # and get then do it again
            worksheet.write( row, column, projectName, boldCellFormat)

            row =  display_project_hierarchy(worksheet, childProject, row, column, boldCellFormat)
    return row
