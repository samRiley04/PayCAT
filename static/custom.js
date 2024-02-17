//PAGELOAD:
// 1. updateSidebarList()
// 2. displayNoSelection() - DONT auto select an entry, and display the empty payslip page.
//PAYSLIP ENTRY CLICKED:
// 1. showPDFEntry(pdfShortName)
//PAYSLIP ENTRY DELETED:
// 1. deletePDFEntry(pdfShortName)
// 2. displayNoSelection()

//IDs in template: 
// -- item-template (Top level card template)
// -- item-date (date of an entry)
// -- item-entry-container (contains all the rows of description/etc. entries)
// -- item-amount (total earned that day)
// -- item-rateunits (going pay rate and how much)
// -- item-description (type of work)
// -- item-total (**generated** by summing all of the amounts in each day)
// -- item-entry (row containing all things for a desc/unitrates/amount set)
// -- payslip-container (contains everything for a given payslip entry - in the left list)
// -- template-storage (contains ALL templates for generating views.)

// ITEMS:
// -- #noContent - basic no content jumbotron.

let selectedSidebarEntry = null
let validSettings = false

// For creating new viewMode or compareMode entry()
// FS means file select
// Need global variables because the value of the DOM element is shortened for readability.
let viewModeFS1path = ""
let compareModeFS1path = ""
let compareModeFS2path = ""


function newViewmode() {
  if (viewModeFS1path == "") {
    //Tell user to select a file and abort
    $("#newEntryModal").find("#viewMode-FS1").addClass("is-invalid")
    return 0;
  } 
  // Otherwise, submit a new POST for server to ingest an entry.
  $.when($.ajax({
      url: "http://localhost:8000/api/studydata",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        "filePath":viewModeFS1path,
        "mode":"view"
      }),
      timeout: 4000, //3 minutes
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      $('#newEntryModal').modal('hide');
      updateSidebarList();
      clearFileSelect();
    }).fail(function (data) {
      alert("failed to add project.")
      //$('#card-container').html("<span class=\"fw-bold text-danger\">Failed to load PDF.</span>")
    });
}

//Shamelessly plagarised from stack overflow
function isValidDate(dateString) {
    // First check for the pattern
    if(!/^\d{1,2}[-/.]\d{1,2}[-/.]\d{4}$/.test(dateString))
        return false;
    dateString = dateString.replace(/[-.]/, "/")
    // Parse the date parts to integers
    var parts = dateString.split("/");
    var day = parseInt(parts[0], 10);
    var month = parseInt(parts[1], 10);
    var year = parseInt(parts[2], 10);

    // Check the ranges of month and year
    if(year < 1000 || year > 3000 || month == 0 || month > 12)
        return false;

    var monthLength = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ];

    // Adjust for leap years
    if(year % 400 == 0 || (year % 100 != 0 && year % 4 == 0))
        monthLength[1] = 29;

    // Check the range of the day
    return day > 0 && day <= monthLength[month - 1];
};

function validateComparemodeInputs() {
  //If the input field is empty, and if its NOT hidden
  let fail = false
  if (compareModeFS1path == "") {
    $("#newEntryModal").find("#compareMode-FS1").addClass("is-invalid")
    abort = true
  } else {
    $("#newEntryModal").find("#compareMode-FS1").removeClass("is-invalid") 
  }
  if (compareModeFS2path == "") {
    $("#newEntryModal").find("#compareMode-FS2").addClass("is-invalid")
    abort = true
  } else {
    $("#newEntryModal").find("#compareMode-FS2").removeClass("is-invalid")
  }

  let daList = []
  if (!$(".compareMode-F1-roster-fields").is("[hidden]")) {
     daList = daList.concat(["#compareMode-empName", "#compareMode-endDate", "#compareMode-startDate"])
  }
  if (!$(".compareMode-F2-roster-fields").is("[hidden]")) {
    daList = daList.concat(["#compareMode-empName2", "#compareMode-endDate2", "#compareMode-startDate2"])
  }
  for (id of daList) {
    if (($(id).val() == "") || (id.includes("Date") && !isValidDate($(id).val())) ) {
      $(id).addClass("is-invalid")
      fail = true
    } else {
      $(id).removeClass("is-invalid")
    }
  }
  if (fail) {return false}
  return true
}

function newComparemode() {
  // INPUT VALIDATION
  if (!validateComparemodeInputs()) {
    //return 0
  }

  // Otherwise, submit a new POST for server to ingest an entry.
  sendObj = {"mode":"compare",
    "filePath":compareModeFS1path,
    "filePath2":compareModeFS2path}

  rosterType = null
  rosterType2 = null
  if (compareModeFS1path.endsWith(".xlsx")) {
    sendObj = {...sendObj, "rosterType": $("#newEntryModal").find("[name=compareMode-RT1]:checked").attr("contentz"),
      "employeeName": $("#compareMode-empName").val(),
      "startDate": $("#compareMode-startDate").val(),
      "endDate": $("#compareMode-endDate").val()
    }
  }
  if (compareModeFS2path.endsWith(".xlsx")) {
    sendObj = {...sendObj, "rosterType2": $("#newEntryModal").find("[name=compareMode-RT2]:checked").attr("contentz"),
      "employeeName2": $("#compareMode-empName2").val(),
      "startDate2": $("#compareMode-startDate2").val(),
      "endDate2": $("#compareMode-endDate2").val()
    }
  }

  // sendObj = {
  //   "mode":"compare",
  //   "filePath":"/Users/sam/Documents/GitHub/PayCAT/test.pdf",
  //   "filePath2":"/Users/sam/Documents/GitHub/PayCAT/TESTING/OPH.xlsx",
  //   "rosterType2":"C",
  //   "employeeName2":"Samuel Riley",
  //   "startDate2":"30-01-2021",
  //   "endDate2":"12-02-2021"
  // }

  $.when($.ajax({
      url: "http://localhost:8000/api/studydata",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(sendObj),
      timeout: 4000, //3 minutes
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      $('#newEntryModal').modal('hide');
      updateSidebarList();
      clearFileSelect();
    }).fail(function(jqXHR) {
      alert(jqXHR["responseJSON"]["message"])
    });
}

//Refreshes the sidebar (which displays all payslips stored in the local shelf DB.)
function updateSidebarList() {
  $.when($.ajax({
      url: "http://localhost:8000/api/studydata",
      type: 'GET',
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      //Clear the sidebar by setting its contents to be only the header.
      $('#side-bar-listgroup').html($('#template-storage > #side-bar-header').clone().attr('id', 'side-bar-header-clone'))
      for (entryID in data["data"]) {
        //for each entry in the shelf database, create a new entry in the sidebar
        let newID = String(entryID)+"-entry"
        let study = data["data"][entryID] //either a "compare" or "view" object
        //"RENDER" A VIEW TYPE STUDY
        if (Object.hasOwn(study, "view")) { //checks if obj contains the key "view"
          $('#side-bar-listgroup').append($('#template-storage > #side-bar-view').clone().attr('id',newID))
          $('#side-bar-listgroup').find('#'+newID).find("#file-title").text(study["view"]["name"])
          $('#side-bar-listgroup').find('#'+newID).find("#sbv-delbutton").attr('onclick', "deleteSidebarEntry("+entryID+"); event.stopPropagation();")
          $('#side-bar-listgroup').find('#'+newID).attr('onclick', "selectSidebarEntry("+entryID+")")
        }
        // "RENDER" A COMPARE TYPE STUDY
        else if (Object.hasOwn(study, "compare")) {
          let file1 = study["compare"][0]["name"];
          let file2 = study["compare"][1]["name"];
          $('#side-bar-listgroup').append($('#template-storage > #side-bar-compare').clone().attr('id',newID))
          //FILE 1
          $('#side-bar-listgroup').find("#"+newID).find("#f1-title").text(file1)
          if (file1.endsWith(".pdf")) {
            $('#side-bar-listgroup').find("#"+newID).find("#f1-file-icon").attr("hidden", false)
          } else if (file1.endsWith(".xlsx")) {
            $('#side-bar-listgroup').find("#"+newID).find("#f1-roster-icon").attr("hidden", false)
          };
          //FILE 2
          $('#side-bar-listgroup').find("#"+newID).find("#f2-title").text(file2)
          if (file2.endsWith(".pdf")) {
            $('#side-bar-listgroup').find("#"+newID).find("#f2-file-icon").attr("hidden", false)
          } else if (file2.endsWith(".xlsx")) {
            $('#side-bar-listgroup').find("#"+newID).find("#f2-roster-icon").attr("hidden", false)
          };
          //buttons
          $('#side-bar-listgroup').find('#'+newID).find("#sbv-delbutton").attr('onclick', "deleteSidebarEntry("+entryID+"); event.stopPropagation();")
          $('#side-bar-listgroup').find('#'+newID).attr('onclick', "selectSidebarEntry("+entryID+")")
        }
        // Is selected?
        if (newID == selectedSidebarEntry) {
          $('#side-bar-listgroup').find('#'+newID).addClass("bg-primary-subtle")
        }
      }
    }).fail(function (data) {
      alert("Failed filling sidebar. Message: " + data["message"]);
    });
}

function selectSidebarEntry(pdfID) {
  // Remove the current 'active state' on all entries, and add it to the selected entry.
  $('#side-bar-listgroup').children('.list-group-item').each(function () {
    this.classList.remove("bg-primary-subtle")
  });
  selectedSidebarEntry = pdfID+"-entry"
  $('#side-bar-listgroup').find("#"+pdfID+"-entry").addClass("bg-primary-subtle");
  // Load the selected entry.
  loadEntry(pdfID);
}

function loadEntry(pdfID) {
  //GET information about it from the database, then fill it out in the main block.
    $.when($.ajax({
      url: "http://localhost:8000/api/studydata/"+pdfID,
      type: 'GET',
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      let compareModeBasic = false
      // --- For VIEW-type entries: ---

      // let newID = "121"
      // $('#content-column').html($("#template-storage").find("#some-shit").clone().attr("id",newID+"-body"))
      // return 1

      if (Object.hasOwn(data["data"], "view")) {
        //Readability: (datesDict is the dictionary of payslip entries with key="23-02-2022" for example.)
        let study = data["data"]["view"]
        let datesDict = study["data"]; //sorry for being confusing. See the API documentation.
        let newID = pdfID+"-entry" //IDs are just an integer, could possibly get lost/cause issues if using only that as ID's?
        //Clear the main container and add the new content type.
        $('#content-column').html($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header"))
        //Then add the body part.
        $('#content-column').append($("#template-storage").find("#viewMode-body").clone().attr("id",newID+"-body"))
        //Now iterate through the data in this entry and generate a card for each date.
        for (date in datesDict) {
          //Clone a new card in the container, rename it's ID as the date, and remove hidden.
          let cardID = date+"-card"
          $('#content-column').find('#'+newID+"-body").find("#card-container").append($("#"+newID+"-body").find("#item-template").clone().attr("id",cardID).removeAttr("hidden"))
          //Uniqify the collapse IDs (generic)
          $('#content-column').find('#'+newID+"-body").find('#'+cardID+" > .card-header").attr("href", "#"+date+"-collapse")
          $('#content-column').find('#'+newID+"-body").find('#'+cardID+" > .collapse").attr("id", date+"-collapse")
          //Fill all the values in the card
          //Date:
          //TODO - 'from date' AND 'to date'.
          $('#content-column').find('#'+newID+"-body").find('#'+cardID).find("#item-date").text(date)       
          //Now work through each contributing item (base hours, OT @ 1.5), filling the text and summing the total amount.
          let sumAmount = 0
          for (let i = 0; i < datesDict[date].length; i++) {
            let entry = datesDict[date][i]
            sumAmount += parseFloat(entry["amount"])
            //'Item entries' are 'text/units+rate/amount' e.g. "BASE HOURS (12@43.223)      $123.45"
            $('#'+newID+"-body").find('#'+cardID).find("#item-entry-container").append($('#'+newID+"-body").find('#'+cardID).find("#item-entry").clone().removeAttr('hidden').attr('id', "item-entry"+i))
            //Only if they're defined, fill units/rate
            if (typeof entry["units"] !== 'undefined') {
              $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").text("("+entry["units"] + "h @ $" + entry["rate"]+")")
            } else {
              $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").text("")            
            }
            //If units are negative, highlight this.
            if (entry["units"] < 0) {
              $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").addClass("text-danger-emphasis")
            }
            if (entry["amount"] < 0)  {
              $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-amount").addClass("text-danger")
            }
            $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-description").text(entry["description"])
            $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-amount").text("$"+entry["amount"])
          }
          //finally record the sum of all amounts
          $('#'+newID+"-body").find('#'+cardID).find("#item-total").text("$"+sumAmount.toFixed(2).toString())
        }
        //Record the heading entries
        $('#'+newID+"-header").find("#header-PPE").text("PPE " + study["payPeriodEnding"])
        $('#'+newID+"-header").find("#header-name-employer").text(study["employeeName"].toUpperCase() + "  /  " + study["employer"].toUpperCase())
        $('#'+newID+"-header").find("#header-totalPTI").text("$"+study["totalPretaxIncome"])
      // --- For COMPARE-type entries: ---
      } else if (Object.hasOwn(data["data"], "compare") && compareModeBasic) {
        //ESSENTIALLY THE SAME SHIT, but twice
        let study = data["data"]["compare"]
        let newID = pdfID+"-entry" //IDs are just an integer, could possibly get lost/cause issues if using only that as ID's?
        //Clear the main container and add the new content type.
        $('#content-column').html($("#template-storage").find("#compareMode-body").clone().attr("id",newID+"-body"))
        let bodyID = "#"+newID+"-body";
        //Then add the header.
        if (study[0]["name"].endsWith(".pdf")) {
          $(bodyID).find("#header-rowcol").find("#card-container-left").append($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header-left"))
        } else if (study[0]["name"].endsWith(".xlsx")) {
          $(bodyID).find("#header-rowcol").find("#card-container-left").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header-left"))
        }
        if (study[1]["name"].endsWith(".pdf")) {
          $(bodyID).find("#header-rowcol").find("#card-container-right").append($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header-right"))
        } else if (study[1]["name"].endsWith(".xlsx")) {
          $(bodyID).find("#header-rowcol").find("#card-container-right").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header-right"))
        }
        
        //Readability:
        //Because I can't do it in a smarter way:
        let todo = [{...study[0], "side":"left"},{...study[1], "side":"right"}]
        //Now iterate through the data in this entry and generate a card for each date.
        for (whichever of todo) { 
          let side = whichever["side"]
          let headerID = "#"+newID+"-header-"+side
          for (date in whichever["data"]) {
            //Clone a new card in the container, rename it's ID as the date, and remove hidden.
            let cardID = side+"-"+date+"-card"
            let templateID = ""
            if (whichever["name"].endsWith(".pdf")) {
              templateID = "#item-template-payslip"
            } else if (whichever["name"].endsWith(".xlsx")) {
              templateID = "#item-template-roster"
            }
            $('#content-column').find(bodyID).find("#body-rowcol").find("#card-container-"+side).append($(bodyID).find(templateID).clone().attr("id",cardID).removeAttr("hidden"))
            //Uniqify the collapse IDs (generic)
            //INTENTIONALLY CREATE DUPLICATE IDS HERE ! - entries with the same date should open and close together, thus should name them identically!
            $('#content-column').find(bodyID).find('#'+cardID+" > .card-header").attr("href", "#"+date+"-collapse")
            $('#content-column').find(bodyID).find('#'+cardID+" > .collapse").attr("id", date+"-collapse")
            //Fill all the values in the card 
            //Date:
            //TODO - 'from date' AND 'to date'.
            $('#content-column').find(bodyID).find('#'+cardID).find("#item-date").text(date)       
            //Now work through each contributing item (base hours, OT @ 1.5), filling the text and summing the total amount.
            let sumAmount = 0
            for (let i = 0; i < whichever["data"][date].length; i++) {
              let entry = whichever["data"][date][i]
              sumAmount += parseFloat(entry["amount"])
              //'Item entries' are 'text/units+rate/amount' e.g. "BASE HOURS (12@43.223)      $123.45"
              $(bodyID).find('#'+cardID).find("#item-entry-container").append($(bodyID).find('#'+cardID).find("#item-entry").clone().removeAttr('hidden').attr('id', "item-entry"+i))
              //Only if they're defined, fill units/rate
              if (typeof entry["units"] !== 'undefined') {
                $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").text("("+entry["units"] + "h @ $" + entry["rate"]+")")
              } else {
                $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").text("")            
              }
              //If units are negative, highlight this.
              if (entry["units"] < 0) {
                $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").addClass("text-danger-emphasis")
              }
              if (entry["amount"] < 0)  {
                $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-amount").addClass("text-danger")
              }
              $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-description").text(entry["description"])
              $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-amount").text("$"+entry["amount"])
            }
            //finally record the sum of all amounts
            $(bodyID).find('#'+cardID).find("#item-total").text("$"+sumAmount.toFixed(2).toString())
          }
          //Record the heading entries
          $('#content-column').find(headerID).find("#header-PPE").text("PPE " + whichever["payPeriodEnding"])
          $('#content-column').find(headerID).find("#header-name-employer").text(whichever["employeeName"].toUpperCase() + "  /  " + whichever["employer"].toUpperCase())
          $('#content-column').find(headerID).find("#header-totalPTI").text("$"+whichever["totalPretaxIncome"])
        }
      } else if (Object.hasOwn(data["data"], "compare")) {
        alert("real compare mode:")
        let study = data["data"]["compare"]
        let newID = pdfID+"-entry-body"
        $('#content-column').html($("#template-storage").find("#compareMode-body-new").clone().attr("id",newID))
        // ADD THE HEADERS
        if (study[0]["name"].endsWith(".pdf")) {
          $("#"+newID).find("#header-rowcol").find("#card-container-left").append($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header-left"))
        } else if (study[0]["name"].endsWith(".xlsx")) {
          $("#"+newID).find("#header-rowcol").find("#card-container-left").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header-left"))
        }
        if (study[1]["name"].endsWith(".pdf")) {
          $("#"+newID).find("#header-rowcol").find("#card-container-right").append($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header-right"))
        } else if (study[1]["name"].endsWith(".xlsx")) {
          $("#"+newID).find("#header-rowcol").find("#card-container-right").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header-right"))
        }
        // FILL THE BODY
        let discrepancies = data["data"]["discrepancies"]
        for (discrepancyDate in discrepancies) {
          // Make a empty template.
          let noticeID = discrepancyDate+"-notice"
          $("#"+newID).find("#body-rowcol").append($("#"+newID).find("#notice-template").clone().attr("id",noticeID))
          $("#"+noticeID).removeAttr('hidden');
          // Fill the card elements.
          todo = {"left":0, "right":1}
          for (side in todo) {
            sideID = side+discrepancyDate+"-disc-card"
            if (Object.hasOwn(study[todo[side]]["data"], discrepancyDate)) { //if the date is in the left list
              //Make a normal entry
              $("#"+noticeID).find("#notice-body-"+side).append($("#"+noticeID).find("#item-template").clone().attr('id',sideID))
              $("#"+sideID).removeAttr('hidden')
              if (study[todo[side]]["name"].endsWith(".pdf")) {
                $("#"+sideID+" > .card-header").addClass("sam-payslip-theme-light")
              } else if (study[todo[side]]["name"].endsWith(".xlsx")) {
                $("#"+sideID+" > .card-header").addClass("sam-roster-theme-light")
              }
              $("#"+sideID).find(".card-header").attr("href", "#"+discrepancyDate+"-disc-collapse")
              $("#"+sideID).find(".collapse").attr("id", discrepancyDate+"-disc-collapse") //Don't specify left or right as both sides should open together if they're the same date.
            } else {
              //Otherwise make a ghost
              $("#"+noticeID).find("#notice-body-"+side).append($(noticeID).find("#item-template-ghost").clone().attr('id',sideID))
              $("#"+sideID).removeAttr('hidden')
              $("#"+sideID).find(".card-header").attr("href", "") //The ghost shouldn't open it's collapse.
              $("#"+sideID).find(".collapse").attr("id", sideID+"-collapse-DONTOPEN")
            }
            
          }

          

          // // Iterate badges, and add them.
          // for (badge in discrepancies[discrepancyDate]["badges"]) {
            
          // }

          // // Iterate highlights, and highlight
          // for (highlight in discrepancies[discrepancyDate]["highlights"]) {

          // }

        }



      } else {
        // ?? what else is there.
        alert("invalid type. Unable to load.")
      }
    }).fail(function (data) {
      alert("Failed to load the selected entry. Reason: " + data["message"]);
    });
}

function deleteSidebarEntry(pdfID) {
  $.when($.ajax({
      url: "http://localhost:8000/api/studydata/"+String(pdfID),
      type: 'DELETE',
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      // If the deleted entry was selected, displayNoSelection()
      if ($('#side-bar-listgroup').find("#"+pdfID+"-entry").hasClass("bg-primary-subtle")) {
        displayNoSelection();
      }
      updateSidebarList();
    }).fail(function (data) {
      alert("Failed deleting entry");
    });
}

function userSelectFile() {
  $.when($.ajax({
    url: "http://localhost:8000/api/FilePath",
    type: 'GET',
    timeout: 160000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    return data["data"];
  }).fail(function (data) {
    alert("Failed to get path. Message: "+data["message"]);
  });
}

//Rests all variables to empty, file-selectors to empty, and removes all invalid labels.
function clearFileSelect() {
  viewModeFS1path = "";
  compareModeFS1path = "";
  compareModeFS2path = "";
  $("#newEntryModal").find("#viewMode-FS1").removeClass("is-invalid")
  $("#newEntryModal").find("#viewMode-FS1").val("")
  $("#newEntryModal").find("#compareMode-FS1").removeClass("is-invalid")
  $("#newEntryModal").find("#compareMode-FS1").val("")
  $("#newEntryModal").find("#compareMode-FS2").removeClass("is-invalid")
  $("#newEntryModal").find("#compareMode-FS2").val("")

  $(".compareMode-F1-roster-fields").find(".btn-check").each(function() {
      $(this).prop("checked", false)
  })
  $(".sam-should-be-checked").each(function() {
    $(this).prop("checked", true)
  })
  $(".compareMode-F1-roster-fields, .compareMode-F2-roster-fields").each(function() {
    $(this).attr('hidden', true)
    $(this).find(".clear-on-reset").each(function() {
      $(this).val("")
    })
  })


  $(".compareMode-F2-roster-fields").each(function() {
    $(this).attr('hidden', true)
  })
}

//fsID includes # already.
function fillFileSelect(fsID) {
  $.when($.ajax({
    url: "http://localhost:8000/api/filepath",
    type: 'GET',
    timeout: 160000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    let filePath = data["data"].split('/')
    //Check if we need to un-hide the options required for a roster file-type.
    unhideOptions = false
    if (String(filePath).endsWith(".xlsx")) {
      unhideOptions = true
    }
    $(fsID).val(filePath[filePath.length -1]) //shortname of the file
    if (fsID == "#viewMode-FS1") {
      viewModeFS1path = data["data"]
      if (unhideOptions) {
        alert("unhide viewmode roster options")
      }
    } else if (fsID == "#compareMode-FS1") {
      compareModeFS1path = data["data"]
      if (unhideOptions) {
        $(".compareMode-F1-roster-fields").each(function() {
          $(this).attr('hidden', false)
        })
      } else {
        $(".compareMode-F1-roster-fields").each(function() {
          $(this).attr('hidden', true)
        })
      }
    } else if (fsID == "#compareMode-FS2") {
      compareModeFS2path = data["data"]
      if (unhideOptions) {
        $(".compareMode-F2-roster-fields").each(function() {
          $(this).attr('hidden', false)
        })
      } else {
        $(".compareMode-F2-roster-fields").each(function() {
          $(this).attr('hidden', true)
        })
      }
    }
  }).fail(function (data) {
    alert("Failed to get path. Message: "+data["message"]);
  });
}

//When no payslip entry is selected, this is the data shown.
function displayNoSelection() {
  $('#content-column').html("")
  $('#content-column').html($('#template-storage > #noContent').clone().attr('id','noContent-clone'))
}

//SETTINGS
function loadExistingSettings() {
    if (validSettings) {
      $("#settingsModal").attr("hidden", false)
      $("#settingsModal").find("#settingsClose").attr("hidden", false)
      $("#settingsModal").find("#settingsCloseLowbutton").attr("hidden", false)
      $("#settingsModal").find("#settings-firsttime-alert").attr("hidden", true)
      $("#settingsModal").attr("data-bs-backdrop", false) //These two not working for some reason???? TODO ***
      $("#settingsModal").attr("data-bs-keyboard", true)
    }

    $.when($.ajax({
    url: "http://localhost:8000/api/settings",
    type: 'GET',
    timeout: 4000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    $("#settingsModal").find("#wage-base-rate-input").removeClass("is-invalid")
    $("#settingsModal").find("#wage-base-rate-invalidDP").attr("hidden", true)
    $("#settingsModal").find("#wage-base-rate-input").val(data["data"]["wage-base-rate"])
    $("#settingsModal").find("#usual-hours-input").val(data["data"]["usual-hours"])
    $("#settingsModal").find("#usual-hours-input").removeClass("is-invalid")
  }).fail(function (data) {
    alert("Failed to get settings. Message: "+data["message"]);
  });
}

function submitSettings(modalID) {
    //resetting validation
    $("#"+modalID).find("#wage-base-rate-invalidFormat").attr("hidden", true)
    $("#"+modalID).find("#wage-base-rate-invalidDP").attr("hidden", true)
    $("#"+modalID).find("#wage-base-rate-input").removeClass("is-invalid")
    $("#"+modalID).find("#usual-hours-input").removeClass("is-invalid")
    $("#"+modalID).find("#usual-hours-invalidFormat").attr("hidden", true)
    $("#"+modalID).find("#usual-hours-invalidSemantically").attr("hidden", true)

    let wage = $("#"+modalID).find("#wage-base-rate-input").val().trim()
    let usualhours = $("#"+modalID).find("#usual-hours-input").val().trim()
    let abort = false
    let checkREdigits = /^(\d+)\.(\d+)$/
    let checkREfourDP = /^(\d+)\.(\d{4})$/
    // Validate Base Rate input field. (regexes come out to: "digits.4 decimal places" only.)
    if (!checkREdigits.test(wage)) {
      $("#"+modalID).find("#wage-base-rate-input").addClass("is-invalid")
      $("#"+modalID).find("#wage-base-rate-invalidFormat").removeAttr("hidden")
      abort = true
    } else if (!checkREfourDP.test(wage)) {
      $("#"+modalID).find("#wage-base-rate-input").addClass("is-invalid")
      $("#"+modalID).find("#wage-base-rate-invalidDP").removeAttr("hidden")
      abort = true
    }
    let checkREdigitsonly = /^(\d+(\.0+)?)$/
    let checkREuslhrs = /(^[2-9](\.0+)?$)|(^1[0-9](\.0+)?$)|(^2[0-4](\.0+)?$)/ //Accepts numbers 2 to 24 +/- ending in .00
    let checkREendwithdec = /\.0+$/
    // Validate Usual Hours input field.
    if (!checkREdigitsonly.test(usualhours)) {
      $("#"+modalID).find("#usual-hours-input").addClass("is-invalid")
      $("#"+modalID).find("#usual-hours-invalidFormat").removeAttr("hidden")
      abort = true
    } else if (!checkREuslhrs.test(usualhours)) {
      $("#"+modalID).find("#usual-hours-input").addClass("is-invalid")
      $("#"+modalID).find("#usual-hours-invalidSemantically").removeAttr("hidden")
      abort = true
    } else if (checkREendwithdec.test(usualhours)) { //trim the .000000 however many zeroes.
      usualhours = usualhours.split(".")[0]
    }
    if (abort) {return 0}

    $.when($.ajax({
    url: "http://localhost:8000/api/settings",
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      "wage-base-rate":wage,
      "usual-hours":usualhours
    }),
    timeout: 4000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
      $("#"+modalID).modal('hide');
      if (!validSettings) {
        //Only really called once ever. If we are saving and this was the initial setting of config, remove that modal.
        validSettings = true
        $("#settingsModal").attr("hidden", false)
        $("#settingsModalFirstTime").remove()
      }
  }).fail(function (data) {
    alert("Failed to set settings. Message: "+data["message"]);
  });
}

function confirmSettingsNotUnset() {
  $.when($.ajax({
    url: "http://localhost:8000/api/settings",
    type: 'GET',
    timeout: 4000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    if (data["data"]["wage-base-rate"] == null || data["data"]["usual-hours"] == null) { //If user needs to set default settings.
      validSettings = false;
    } else {
      validSettings = true;
    }

    if (!validSettings) {
      //Modify the a new config modal to be un-closable.
      $("body").append($("#settingsModal").clone().attr('id', 'settingsModalFirstTime'))
      $("#settingsModal").attr("hidden", true)
      $("#settingsModalFirstTime").find("#settingsClose").attr("hidden", true)
      $("#settingsModalFirstTime").find("#settingsCloseLowbutton").attr("hidden", true)
      $("#settingsModalFirstTime").find("#settings-firsttime-alert").attr("hidden", false)
      $("#settingsModalFirstTime").find("#settings-save-button").attr("onclick", "submitSettings('settingsModalFirstTime')")
      $("#settingsModalFirstTime").attr("data-bs-backdrop", "static")
      $("#settingsModalFirstTime").attr("data-bs-keyboard", "false")
      // Open the config modal.
      $('#settingsModalFirstTime').modal('show');

      // $("#settingsModal").find("#settingsClose").attr("hidden", true)
      // $("#settingsModal").find("#settingsCloseLowbutton").attr("hidden", true)
      // $("#settingsModal").find("#settings-firsttime-alert").attr("hidden", false)
      // $("#settingsModal").attr("data-bs-backdrop", "static")
      // $("#settingsModal").attr("data-bs-keyboard", "false")
      // // Open the config modal.
      // $('#settingsModal').modal('show');
    }
    return 1
  }).fail(function (data) {
    alert("Unable to load configuration from server. Message: "+data["message"]);
  });

}

//Event listeneres etc..
function setup() {
  //FOR COMPAREMODE - Resets the value on clicking the file selectors
  // $("#compareMode-FS1").on('click touchstart', function() {
  //   $(this).val('');
  //   compareModeFS1 = ""
  // });
  // $("#compareMode-FS2").on('click touchstart', function() {
  //   $(this).val('');
  //   compareModeFS2 = ""
  // });
}
 
confirmSettingsNotUnset()
setup()

