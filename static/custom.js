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

function newComparemode() {
  if (compareModeFS1path == "") {
    //Tell user to select a file and abort
    $("#newEntryModal").find("#compareMode-FS1").addClass("is-invalid")
  } 
  if (compareModeFS2path == "") {
    $("#newEntryModal").find("#compareMode-FS2").addClass("is-invalid")
  }
  if (compareModeFS2path == "" || compareModeFS1path == "") {
    return 0;
  }

  // Otherwise, submit a new POST for server to ingest an entry.
  $.when($.ajax({
      url: "http://localhost:8000/api/studydata",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
    "filePath":compareModeFS1path,
    "filePath2":compareModeFS2path,
    "mode":"compare"
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
      alert("failed to add PDF.")
      //$('#card-container').html("<span class=\"fw-bold text-danger\">Failed to load PDF.</span>")
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
        if (data["data"][entryID]["mode"] == "view") {
          $('#side-bar-listgroup').append($('#template-storage > #side-bar-view').clone().attr('id',newID))
          $('#side-bar-listgroup').find('#'+newID).find("#file-title").text(data["data"][entryID]["name"])
          $('#side-bar-listgroup').find('#'+newID).find("#sbv-delbutton").attr('onclick', "deleteSidebarEntry("+entryID+"); event.stopPropagation();")
          $('#side-bar-listgroup').find('#'+newID).attr('onclick', "selectSidebarEntry("+entryID+")")
        } else if (data["data"][entryID]["mode"] == "compare") {
          let file1 = "jeff.pdf";
          let file2 = data["data"][entryID]["name"];
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
      // --- For VIEW-type entries: ---
      if (data["data"]["mode"] == "view") {
        let newID = pdfID+"-entry" //IDs are just an integer, could possibly get lost/cause issues if using only that as ID's?
        //Clear the main container and add the new content type.
        $('#content-column').html($('#template-storage').find("#viewMode-header").clone().attr("id",newID+"-header"))
        //Then add the body part.
        $('#content-column').append($("#template-storage").find("#viewMode-body").clone().attr("id",newID+"-body"))
        //Readability: (datesDict is the dictionary of payslip entries with key="23-02-2022" for example.)
        datesDict = data["data"]["data"];
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
        $('#'+newID+"-header").find("#header-PPE").text("PPE " + data["data"]["payPeriodEnding"])
        $('#'+newID+"-header").find("#header-name-employer").text(data["data"]["employeeName"].toUpperCase() + "  /  " + data["data"]["employer"].toUpperCase())
        $('#'+newID+"-header").find("#header-totalPTI").text("$"+data["data"]["totalPretaxIncome"])
      // --- For COMPARE-type entries: ---
      } else if (data["data"]["mode"] == "compare") {
        //ESSENTIALLY THE SAME SHIT, but twice
        let newID = pdfID+"-entry" //IDs are just an integer, could possibly get lost/cause issues if using only that as ID's?
        //Clear the main container and add the new content type.
        $('#content-column').html($("#template-storage").find("#compareMode-body").clone().attr("id",newID+"-body"))
        // $('#content-column').html($('#template-storage').find("#viewMode-header").clone().attr("id",newID+"-header"))
        let bodyID = "#"+newID+"-body";
        //Then add the header.
        if (data["data"]["name"].endsWith(".pdf")) {
          $(bodyID).find("#card-container-left").append($('#template-storage').find("#viewMode-header").clone().attr("id",newID+"-header"))
        } else if (data["data"]["name"].endsWith(".xlsx")) {
          $(bodyID).find("#card-container-left").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header"))
        }
        if (data["data"]["name2"].endsWith(".pdf")) {
          $(bodyID).find("#card-container-right").append($('#template-storage').find("#viewMode-header").clone().attr("id",newID+"-header"))
        } else if (data["data"]["name"].endsWith(".xlsx")) {
          $(bodyID).find("#card-container-right").append($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header"))
        }
        
        //Readability:
        todo = [{
          "datesDict": data["data"]["data"],
          "side":"left",
          "fileName":data["data"]["name"]
        }, {
          "datesDict": data["data"]["data2"],
          "side":"right",
          "fileName":data["data"]["name2"]
        }]
        //Now iterate through the data in this entry and generate a card for each date.
        for (whichever of todo) { 
          for (date in whichever["datesDict"]) {
            let side = whichever["side"]
            //Clone a new card in the container, rename it's ID as the date, and remove hidden.
            let cardID = side+"-"+date+"-card"
            let templateID = ""
            if (whichever["fileName"].endsWith(".pdf")) {
              templateID = "#item-template-payslip"
            } else if (whichever["fileName"].endsWith(".xlsx")) {
              templateID = "#item-template-roster"
            }
            $('#content-column').find(bodyID).find("#card-container-"+side).append($(bodyID).find(templateID).clone().attr("id",cardID).removeAttr("hidden"))
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
            for (let i = 0; i < whichever["datesDict"][date].length; i++) {
              let entry = whichever["datesDict"][date][i]
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
        }
        //Record the heading entries
        $('#'+newID+"-header").find("#header-PPE").text("PPE " + data["data"]["payPeriodEnding"])
        $('#'+newID+"-header").find("#header-name-employer").text(data["data"]["employeeName"].toUpperCase() + "  /  " + data["data"]["employer"].toUpperCase())
        $('#'+newID+"-header").find("#header-totalPTI").text("$"+data["data"]["totalPretaxIncome"])
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
    $(fsID).val(filePath[filePath.length -1])
    if (fsID == "#viewMode-FS1") {
      viewModeFS1path = data["data"]
    } else if (fsID == "#compareMode-FS1") {
      compareModeFS1path = data["data"]
    } else if (fsID == "#compareMode-FS2") {
      compareModeFS2path = data["data"]
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

confirmSettingsNotUnset()

