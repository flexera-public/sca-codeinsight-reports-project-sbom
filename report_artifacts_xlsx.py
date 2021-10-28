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
def generate_xlsx_report(reportData, reportNameBase):
    logger.info("    Entering generate_xlsx_report")

    projectName = reportData["projectName"]
    fileNameTimeStamp = reportData["fileNameTimeStamp"] 
    inventoryData = reportData["inventoryData"]
    projectList = reportData["projectList"]
    reportOptions = reportData["reportOptions"]
    projectHierarchy = reportData["projectHierarchy"]

    xlsxFile = reportNameBase + ".xlsx"

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
        
        hierachyWorksheet.write(0, 0, "Report Generated: %s" %datetime.strptime(fileNameTimeStamp, "%Y%m%d-%H%M%S").strftime("%B %d, %Y at %H:%M:%S"))
        hierachyWorksheet.write(1, 0, "Report Version: %s" %_version.__version__)
        
        hierachyWorksheet.write('B4', projectName, hierarchyCellFormat) # Row 3, column 1
        row=3
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

    # If there is no hierarchy add report details 
    if len(projectList) == 1:
        detailsWorksheet.write(0, column+1, "Report Generated: %s" %datetime.strptime(fileNameTimeStamp, "%Y%m%d-%H%M%S").strftime("%B %d, %Y at %H:%M:%S"))
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
        componentUrl = inventoryData[inventoryID]["componentUrl"]
        componentVersionName = inventoryData[inventoryID]["componentVersionName"]
        selectedLicenseName = inventoryData[inventoryID]["selectedLicenseName"]
        selectedLicenseUrl = inventoryData[inventoryID]["selectedLicenseUrl"]
        selectedLicenseName = inventoryData[inventoryID]["selectedLicenseName"]
        projectLink = inventoryData[inventoryID]["projectLink"]
        hasVulnerabilities = inventoryData[inventoryID]["hasVulnerabilities"]

        logger.debug("            Project Name:  %s --> Inventory Item %s" %(projectName, inventoryItemName))

        # Now write each row of inventory data
        column=0
        
        if len(projectList) > 1:
            detailsWorksheet.write(row, column, projectName, cellFormat)
            column+=1
        
        #  Is there a valid URL to link to?
        if componentUrl == "N/A":
            detailsWorksheet.write(row, column, componentName, cellFormat)
        else:
            detailsWorksheet.write_url(row, column, componentUrl, cellLinkFormat, string=componentName)
        column+=1
        

        # Is it a valid version?
        if componentVersionName == "N/A":
            detailsWorksheet.write(row, column, "", cellFormat)
        else:
            detailsWorksheet.write(row, column, componentVersionName, cellFormat)
        column+=1

        # Is it a valid license?
        if selectedLicenseName == "I don't know":
            detailsWorksheet.write(row, column, "", cellFormat)
        else:
             #  Is there a valid URL to link to?
            if selectedLicenseUrl == "":   
                detailsWorksheet.write(row, column, selectedLicenseName, cellFormat)
            else:
                detailsWorksheet.write_url(row, column, selectedLicenseUrl, cellLinkFormat, string=selectedLicenseName)

        column+=1

        if reportOptions["includeVulnerabilities"]:
            if hasVulnerabilities:
                detailsWorksheet.write(row, column, "Yes", cellFormat)
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
