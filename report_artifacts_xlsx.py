'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Oct 27 2021
File : report_artifacts_xlsx.py
'''

import logging
from datetime import datetime
import xlsxwriter

import _version
import report_branding.xlsx.xlsx_formatting

logger = logging.getLogger(__name__)

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

    # Are there child projects involved?  If so have the file name reflect this fact
    if len(projectList)==1:
        xlsxFile = projectNameForFile + "-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx"
    else:
        xlsxFile = projectNameForFile + "-with-children-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx" 

    # Create the workbook/worksheet for storying the data
    workbook = xlsxwriter.Workbook(xlsxFile)

    cellFormat = workbook.add_format(report_branding.xlsx.xlsx_formatting.standardCellFormatProperties)
    cellLinkFormat = workbook.add_format(report_branding.xlsx.xlsx_formatting.linkCellFormatProperties)
    tableHeaderFormat = workbook.add_format(report_branding.xlsx.xlsx_formatting.tableHeaderFormatProperties)
    hierarchyCellFormat = workbook.add_format(report_branding.xlsx.xlsx_formatting.hierarchyCellFormatProperties)

    ###############################################################################################
    # Do we need a hierarchy chart?
    if len(projectList) > 1:

        hierachyWorksheet = workbook.add_worksheet('Project Hierarchy')
        hierachyWorksheet.hide_gridlines(2)
        hierachyWorksheet.write('B2', projectName, hierarchyCellFormat) # Row 2, column 1
        row=1
        column=1
        display_project_hierarchy(hierachyWorksheet, projectHierarchy, row, column, hierarchyCellFormat)

    ############################################################
    # Fill out the SBOM details worksheet
    detailsWorksheet = workbook.add_worksheet('SBOM')
    detailsWorksheet.hide_gridlines(2) 

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
    
    if reportOptions["includeVulnerabilities"]:
        detailsWorksheet.set_column(column, column, 25) 
        tableHeaders.append("VULNERABILITIES")
        column+=1

    detailsWorksheet.write(0, column+1, "Report Generated: %s" %(datetime.now().strftime("%B %d, %Y at %H:%M:%S")))
    detailsWorksheet.write(1, column+1, "Report Version: %s" %_version.__version__)

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

        # Now write each row of inventory data
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
        childProjects = parentProject["childProject"]
        childProjects.sort(key=lambda item: item.get("name"))
        
        for childProject in childProjects:
            projectName = childProject["name"]
            # Add this ID to the list of projects with other child projects
            # and get then do it again
            worksheet.write( row, column, projectName, boldCellFormat)

            row =  display_project_hierarchy(worksheet, childProject, row, column, boldCellFormat)
    return row
