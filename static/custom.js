let selectedSidebarEntry = null
let validSettings = false

// For creating new viewMode or compareMode entry()
// FS means file select
// Need global variables because the value of the DOM element is shortened for readability (and thus doesn't hold the full path).
let viewModeFS1path = ""
let compareModeFS1path = ""
let compareModeFS2path = ""

//Not used
const BADGES_RED = ["Negative hours"]
const BADGES_YELLOW = []

//Shamelessly plagarised from stack overflow, and modified for non US dates
function isValidDate(dateString) {
    // First check for the pattern
    if(!/^\d{1,2}[-/.]\d{1,2}[-/.]\d{4}$/.test(dateString))
        return false;
    dateString = dateString.replaceAll(/[-.]/g, "/")
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

function zeroPadDate(dateString) { //ALSO sanitises date strings to use dashes only
  let dParts = dateString.replaceAll(/[-/.]/g, "-").split("-")
  if (dParts[0].length != 2) {
    dParts[0] = "0"+dParts[0]
  }
  if (dParts[1].length != 2) {
    dParts[1] = "0"+dParts[1]
  }
  return dParts.join("-");
}

function filterUniqueDates(data) {
  const lookup = new Set();
  
  return data.filter(date => {
     const serialised = date.getTime();
    if (lookup.has(serialised)) {
      return false;
    } else { 
      lookup.add(serialised);
      return true;
    }
  })
}

// Partly plagarised from stack overflow
function numberWithCommas(x) {
    return x.toString().replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",");
}

function prettyMoneyString(anyFloat) {
  if (typeof anyFloat == "undefined" || isNaN(anyFloat)) {
    return ""
  } 
  let strVersion = "$"+numberWithCommas(anyFloat.toFixed(2).toString())
  if (strVersion[1] == "-") { // if negative, swap the dollar and minus signs around
    strVersion = "-$"+numberWithCommas(strVersion.substring(2).toString())
  }
  return strVersion
}

function validateComparemodeInputs() {
  //If the input field is empty, and if its NOT hidden
  let fail = false
  if (compareModeFS1path == "") {
    $("#newEntryModal").find("#compareMode-FS1").addClass("is-invalid")
    fail = true
  } else {
    $("#newEntryModal").find("#compareMode-FS1").removeClass("is-invalid") 
  }
  if (compareModeFS2path == "") {
    $("#newEntryModal").find("#compareMode-FS2").addClass("is-invalid")
    fail = true
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
  if (fail) { return false }
  return true
}

function validateViewmodeInputs() {
  //If the input field is empty, and if its NOT hidden
  let fail = false
  if (viewModeFS1path == "") {
    $("#newEntryModal").find("#viewMode-FS1").addClass("is-invalid")
    fail = true
  } else {
    $("#newEntryModal").find("#viewMode-FS1").removeClass("is-invalid") 
  }

  let daList = []
  if (!$(".viewMode-roster-fields").is("[hidden]")) {
     daList = daList.concat(["#viewMode-empName", "#viewMode-endDate", "#viewMode-startDate"])
  }

  for (id of daList) {
    if (($(id).val() == "") || (id.includes("Date") && !isValidDate($(id).val())) ) {
      $(id).addClass("is-invalid")
      fail = true
    } else {
      $(id).removeClass("is-invalid")
    }
  }
  if (fail) { return false }
  return true
}

function newViewmode() {
  if (!validateViewmodeInputs()) {
    return 0;
  } 
  sendObj = {
    "mode":"view",
    "filePath":viewModeFS1path
  }

  if (viewModeFS1path.endsWith(".xlsx")) {
    sendObj = {...sendObj, "rosterType": $("#newEntryModal").find("[name=viewMode-RT]:checked").attr("contentz"),
      "employeeName": $("#viewMode-empName").val(),
      "startDate": zeroPadDate($("#viewMode-startDate").val()),
      "endDate": zeroPadDate($("#viewMode-endDate").val())
    }
  }

  // Otherwise, submit a new POST for server to ingest an entry.
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
      selectSidebarEntry(Object.keys(data["data"])[0]); //Only returns one entryID, which is the one just created.
    }).fail(function (jqXHR) {
      alert(jqXHR["responseJSON"]["message"])
    });
}

function newComparemode() {
  // INPUT VALIDATION
  if (!validateComparemodeInputs()) {
    return 0
  }

  // Otherwise, submit a new POST for server to ingest an entry.
  sendObj = {"mode":"compare",
    "filePath":compareModeFS1path,
    "filePath2":compareModeFS2path}

  if (compareModeFS1path.endsWith(".xlsx")) {
    sendObj = {...sendObj, "rosterType": $("#newEntryModal").find("[name=compareMode-RT1]:checked").attr("contentz"),
      "employeeName": $("#compareMode-empName").val(),
      "startDate": zeroPadDate($("#compareMode-startDate").val()),
      "endDate": zeroPadDate($("#compareMode-endDate").val())
    }
  }
  if (compareModeFS2path.endsWith(".xlsx")) {
    sendObj = {...sendObj, "rosterType2": $("#newEntryModal").find("[name=compareMode-RT2]:checked").attr("contentz"),
      "employeeName2": $("#compareMode-empName2").val(),
      "startDate2": zeroPadDate($("#compareMode-startDate2").val()),
      "endDate2": zeroPadDate($("#compareMode-endDate2").val())
    }
  }

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
      selectSidebarEntry(Object.keys(data["data"])[0]);
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

//This is a disgusting function please dont crucify me for it.
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
        if (study["name"].endsWith(".pdf")) {
          $('#content-column').html($('#template-storage').find("#payslip-header").clone().attr("id",newID+"-header"))
        } else if (study["name"].endsWith(".xlsx")) {
          $('#content-column').html($('#template-storage').find("#roster-header").clone().attr("id",newID+"-header"))
        }
        //Then add the body part.
        $('#content-column').append($("#template-storage").find("#viewMode-body").clone().attr("id",newID+"-body"))
        //Now iterate through the data in this entry and generate a card for each date.
        for (date in datesDict) {
          //Clone a new card in the container, rename it's ID as the date, and remove hidden.
          let cardID = date+"-card"
          $('#content-column').find('#'+newID+"-body").find("#card-container").append($("#"+newID+"-body").find("#item-template").clone().attr("id",cardID).removeAttr("hidden"))
          if (study["name"].endsWith(".pdf")) {
            $('#content-column').find("#"+cardID+" > .card-header").addClass("sam-payslip-theme-light")
          } else if (study["name"].endsWith(".xlsx")) {
            $('#content-column').find("#"+cardID+" > .card-header").addClass("sam-roster-theme-light")
          }
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
            if ((typeof entry["units"] !== 'undefined' && /\d+/.test(entry["units"].replace(".","")))) {
              $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-unitsrate").text("("+entry["units"] + "h @ " + entry["rate"]+")")
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
            $('#'+newID+"-body").find('#'+cardID).find("#item-entry"+i).find("#item-amount").text(prettyMoneyString(parseFloat(entry["amount"]))) 
          }
          //finally record the sum of all amounts
          if (sumAmount < 0) {
              $('#'+newID+"-body").find('#'+cardID).find("#item-total").removeClass("text-success")
              $('#'+newID+"-body").find('#'+cardID).find("#item-total").addClass("text-danger")
            }
          $('#'+newID+"-body").find('#'+cardID).find("#item-total").text(prettyMoneyString(sumAmount))
        }
        //Record the heading entries
        $('#'+newID+"-header").find("#header-PPE").text("PPE " + study["payPeriodEnding"])
        $('#'+newID+"-header").find("#header-name-employer").text(study["employeeName"].toUpperCase() + "  /  " + study["employer"].toUpperCase())
        $('#'+newID+"-header").find("#header-totalPTI").text(prettyMoneyString(parseFloat(study["totalPretaxIncome"])))
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
              $(bodyID).find('#'+cardID).find("#item-entry"+i).find("#item-amount").text(prettyMoneyString(parseFloat(entry["amount"])))
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
        //Do global discrepancy alerts
        let x = 1
        for (alertDesc of data["data"]["globalDiscrepancies"]) {
          $("#"+newID).find("#body-rowcol").prepend($("#"+newID).find("#global-alert-template").clone().attr('id',newID+"-gblalert-"+x.toString()).removeAttr('hidden'))
          $("#"+newID).find("#"+newID+"-gblalert-"+x.toString()).find("#alert-text").text(alertDesc)
          x+=1
        }

        // FILL THE BODY
        let discrepancies = data["data"]["discrepancies"]
        $("#"+newID).find("#body-rowcol").find("#discrepancies-header").text("DISCREPANCIES ("+Object.keys(discrepancies).length+")")
        for (discrepancyDate in discrepancies) {
          // Make a empty template.
          let noticeID = discrepancyDate+"-notice"
          $("#"+newID).find("#body-rowcol").append($("#"+newID).find("#notice-template").clone().attr("id",noticeID))
          $("#"+noticeID).removeAttr('hidden');
          // BADGES and descriptions
          let uniqueList = []
          for (badge of discrepancies[discrepancyDate]["badges"]) {
            let bTitle = Object.keys(badge)[0] //only one key per object for a badge, so this is safe
            if (!uniqueList.includes(bTitle)) {
              if (BADGES_RED.includes(bTitle)) {
                $("#"+noticeID).find("#notice-header-badges").append("<span class='badge bg-danger'>"+bTitle+"</span> ") //end space intentional, to separate sequential badges
              } else {
                $("#"+noticeID).find("#notice-header-badges").append("<span class='badge bg-secondary'>"+bTitle+"</span> ")
              }
              uniqueList.push(bTitle)
            }
            if (BADGES_RED.includes(bTitle)) {
              $("#"+noticeID).find("#notice-header-collapse").append($("#"+noticeID).find("#notice-header-collapse > #badge-desc").clone().attr('id',noticeID+"-"+bTitle.replace(" ","-")).prepend(badge[bTitle]).removeAttr('hidden').addClass("text-danger"))
            } else {
              $("#"+noticeID).find("#notice-header-collapse").append($("#"+noticeID).find("#notice-header-collapse > #badge-desc").clone().attr('id',noticeID+"-"+bTitle.replace(" ","-")).prepend(badge[bTitle]).removeAttr('hidden'))
            }
            //If it's a red badge, needs a red description
          }

          // Fill the card elements. Also highlight.
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
              $("#"+noticeID).find("#notice-body-"+side).append($("#"+noticeID).find("#item-template-ghost").clone().attr('id',sideID))
              $("#"+sideID).removeAttr('hidden')
              $("#"+sideID).find(".card-header").attr("href", "#"+discrepancyDate+"-disc-collapse") //The ghost shouldn't open it's collapse.
              $("#"+sideID).find(".collapse").attr("id", sideID+"-collapse-DONTOPEN")
            }
            $("#"+noticeID).find("#notice-header-collapse").attr("id",discrepancyDate+"-disc-collapse")
            $("#"+sideID).find("#item-date").text(discrepancyDate)

            $('#content-column').find("#"+newID+"-header-"+side).find("#header-PPE").text("PPE " + study[todo[side]]["payPeriodEnding"])
            $('#content-column').find("#"+newID+"-header-"+side).find("#header-name-employer").text(study[todo[side]]["employeeName"].toUpperCase() + "  /  " + study[todo[side]]["employer"].toUpperCase())
            $('#content-column').find("#"+newID+"-header-"+side).find("#header-totalPTI").text("$"+study[todo[side]]["totalPretaxIncome"])  

            let sumAmount = 0
            let givenDateEntry = study[todo[side]]["data"][discrepancyDate]
            //Sometimes a date entry is not in both lists (e.g. in "Shift missing error")
            if (typeof givenDateEntry == 'undefined'){
              continue
              //No need to fill it's hours types entries in that case.
            }
            //ITERATE hour types and fill them out.
            for (let i = 0; i < givenDateEntry.length; i++) {
              let entry = givenDateEntry[i]
              sumAmount += parseFloat(entry["amount"])
              //'Item entries' are 'text/units+rate/amount' e.g. "BASE HOURS (12@43.223)      $123.45"
              $("#"+sideID).find("#item-entry-container").append($('#'+sideID).find("#item-entry").clone().removeAttr('hidden').attr('id', "item-entry"+i))
              $("#"+sideID).find("#item-entry"+i).removeAttr('hidden')
              //Only if they're defined, fill units/rate
              if (typeof entry["units"] !== 'undefined' && /\d+/.test(entry["units"].replace(".",""))) { //this regex skips units/rates entries that aren't numbers
                $("#"+sideID).find("#item-entry"+i).find("#item-units").text("("+entry["units"] + "h")
                $("#"+sideID).find("#item-entry"+i).find("#item-units").clone()
                $("#"+sideID).find("#item-entry"+i).find("#item-rate").text(parseFloat(entry["rate"])+")")
                $("#"+sideID).find("#item-entry"+i).find("#item-entry-at").removeAttr('hidden')
              }
              //If units are negative, emphasise this.
              if (entry["units"] < 0) {
                $("#"+sideID).find("#item-entry"+i).find("#item-unitsrate").addClass("text-danger-emphasis")
              }
              if (entry["amount"] < 0)  {
                $("#"+sideID).find("#item-entry"+i).find("#item-amount").addClass("text-danger")
              }
              $("#"+sideID).find("#item-entry"+i).find("#item-description").text(entry["description"])
              $("#"+sideID).find("#item-entry"+i).find("#item-amount").text(prettyMoneyString(parseFloat(entry["amount"])))
              //HIGHLIGHTING
              for (highlight of discrepancies[discrepancyDate]["highlights"]) {
                if (Object.keys(highlight)[0] == entry["description"]) { //again, only one key per obj
                  //We need to highlight something in this hours-type entry.
                  if (highlight[Object.keys(highlight)[0]] == "description") {
                    $("#"+sideID).find("#item-entry"+i).find("#item-description").addClass("mark")  
                  } else {
                    //If rate/units/amount are wrong, then total amount has to be marked also.
                    $("#"+sideID).find("#item-total").addClass("mark") //this will be called multiple times, but is a far simpler implementation than saving a random variable to check later on
                    if (highlight[entry["description"]] == "rate") {
                      $("#"+sideID).find("#item-entry"+i).find("#item-rate").addClass("mark")
                    } else if (highlight[entry["description"]] == "units") {
                      $("#"+sideID).find("#item-entry"+i).find("#item-units").addClass("mark")
                    } else if (highlight[entry["description"]] == "amount") {
                      $("#"+sideID).find("#item-entry"+i).find("#item-amount").addClass("mark")
                    }
                  }
                }
              }
            }
            if (sumAmount < 0) {
              $("#"+sideID).find("#item-total").removeClass("text-success")
              $("#"+sideID).find("#item-total").addClass("text-danger")
            }
            $("#"+sideID).find("#item-total").text(prettyMoneyString(sumAmount))      
          }
        }
        $("#"+newID).find("#body-rowcol").append($("#full-comparison-header").clone().attr('id',newID+"-comparison-header").removeAttr('hidden'))
        //---------------------//---------------------//---------------------//---------------------
        //Clear the main container and add the new content type.
        $("#"+newID).find("#body-rowcol").append($("#template-storage").find("#compareMode-body").clone().attr("id",newID+"-body"))
        let bodyID = "#"+newID+"-body";
        //Readability:
        //Because I can't do it in a smarter way:
        todo = [{...study[0], "side":"left"},{...study[1], "side":"right"}]
        //Make a unique dates list
        let allDates = []
        for (side of todo) {
          for (key of Object.keys(side["data"])) {
            kbits = key.replaceAll(/[-/.]/g, "-").split("-")
            allDates.push(new Date(kbits[2], kbits[1]-1, kbits[0]))
          }
        }
        let uniqueDates = filterUniqueDates(allDates)
        uniqueDates.sort(function(a,b){return a - b;});
        //Now iterate through the data in this entry and generate a card for each date.
        let uniqueDateStrings = []
        for (date of uniqueDates) {
          uniqueDateStrings.push(date.toLocaleDateString("en-GB", { // you can use undefined as first argument
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          }).replaceAll("/", "-"))
        }
        //This was such a dumb way to make this list.
        for (date of uniqueDateStrings) {
          let cardholderID = newID+"-"+date+"cardholder"
          $('#'+newID).find("#body-rowcol").append($("#template-storage").find("#fc-cardholder-template").clone().attr("id",cardholderID).removeAttr("hidden"))
          for (whichever of todo) { 
            if (!Object.hasOwn(whichever["data"], date)) {
              continue
              //There's no reason to make a card if it's not included in one side's list.
            }
            let side = whichever["side"]
            //Clone a new card in the container, rename it's ID as the date, and remove hidden.
            let cardID = side+"-"+date+"-card"
            let templateID = ""
            $("#content-column").find("#"+cardholderID+" > #card-container-"+side).append($("#template-storage").find("#compareMode-body-new").find("#item-template").clone().attr('id', cardID).removeAttr('hidden')) //theres actually two item templates (viewMode one, and comparemode one. The other not removed for legacy's sake)
            if (whichever["name"].endsWith(".pdf")) {
              $("#"+cardID+" > .card-header").addClass("sam-payslip-theme-light")
            } else if (whichever["name"].endsWith(".xlsx")) {
              $("#"+cardID+" > .card-header").addClass("sam-roster-theme-light")
            }
            //Uniqify the collapse IDs (generic)
            //INTENTIONALLY CREATE DUPLICATE IDS HERE ! - entries with the same date should open and close together, thus should name them identically!
            $('#content-column').find('#'+cardID+" > .card-header").attr("href", "#"+date+"-collapse")
            $('#content-column').find('#'+cardID+" > .collapse").attr("id", date+"-collapse")
            //Fill all the values in the card 
            //Date:
            //TODO - 'from date' AND 'to date'.
            $('#content-column').find('#'+cardID).find("#item-date").text(date)       
            //Now work through each contributing item (base hours, OT @ 1.5), filling the text and summing the total amount.
            let sumAmount = 0
            //There is SO MUCH DUPLICATE CODE IN THIS FUNCTION FUCK
            for (let i = 0; i < whichever["data"][date].length; i++) {
              let entry = whichever["data"][date][i]
              sumAmount += parseFloat(entry["amount"])
              //'Item entries' are 'text/units+rate/amount' e.g. "BASE HOURS (12@43.223)      $123.45"
              $("#"+cardID).find("#item-entry-container").append($('#'+cardID).find("#item-entry").clone().removeAttr('hidden').attr('id', "item-entry"+i))
              $("#"+cardID).find("#item-entry"+i).removeAttr('hidden')
              //Only if they're defined, fill units/rate
              if (typeof entry["units"] !== 'undefined' && /\d+/.test(entry["units"].replace(".",""))) { //this regex skips units/rates entries that aren't numbers
                $("#"+cardID).find("#item-entry"+i).find("#item-units").text("("+entry["units"] + "h")
                $("#"+cardID).find("#item-entry"+i).find("#item-units").clone()
                $("#"+cardID).find("#item-entry"+i).find("#item-rate").text(parseFloat(entry["rate"])+")")
                $("#"+cardID).find("#item-entry"+i).find("#item-entry-at").removeAttr('hidden')
              }
              //If units are negative, emphasise this.
              if (entry["units"] < 0) {
                $("#"+cardID).find("#item-entry"+i).find("#item-unitsrate").addClass("text-danger-emphasis")
              }
              if (entry["amount"] < 0)  {
                $("#"+cardID).find("#item-entry"+i).find("#item-amount").addClass("text-danger")
              }
              $("#"+cardID).find("#item-entry"+i).find("#item-description").text(entry["description"])
              $("#"+cardID).find("#item-entry"+i).find("#item-amount").text(prettyMoneyString(parseFloat(entry["amount"])))
            }
            if (sumAmount < 0) {
              $("#"+cardID).find("#item-total").removeClass("text-success")
              $("#"+cardID).find("#item-total").addClass("text-danger")
            }
            $("#"+cardID).find("#item-total").text(prettyMoneyString(sumAmount)) 
            }
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

//Rests all variables to empty, file-selectors to empty, removes all invalid labels, and pre-fills employee-name.
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

  $(".compareMode-F1-roster-fields, .compareMode-F2-roster-fields, .viewMode-roster-fields").find(".btn-check").each(function() {
      $(this).prop("checked", false)
  })
  $(".sam-should-be-checked").each(function() {
    $(this).prop("checked", true)
  })
  $(".compareMode-F1-roster-fields, .compareMode-F2-roster-fields, .viewMode-roster-fields").each(function() {
    $(this).attr('hidden', true)
    $(this).find(".clear-on-reset").each(function() {
      $(this).val("")
    })
  })

  //Prefill employee-name from the stored settings.
  $.when($.ajax({
    url: "http://localhost:8000/api/settings",
    type: 'GET',
    timeout: 4000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    $("#newEntryModal").find("#viewMode-empName, #compareMode-empName, #compareMode-empName2").each(function() {
      $(this).val(data["data"]["employee-name"])
    })
  }).fail(function (data) {
    alert("Failed preload settings. Message: "+data["message"]);
  });
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
        $(".viewMode-roster-fields").each(function() {
          $(this).attr('hidden', false)
        })
      } else {
        $(".viewMode-roster-fields").each(function() {
          $(this).attr('hidden', true)
        })
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

function changeAllCollapses(containerID, action) {
if (action === "show") {
  $("#"+containerID).find(".collapse").each(function () {
    let currentElement = new bootstrap.Collapse(this, {toggle:false})
    currentElement.show()
  })
} else if (action === "hide") {
  $("#"+containerID).find(".collapse").each(function () {
    let currentElement = new bootstrap.Collapse(this, {toggle:false})
    currentElement.hide()
  })
}
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
    $("#settingsModal").find("#employee-name-input").val(data["data"]["employee-name"])
    if (data["data"]["which-state-version"] == "WA") {
      $("#settingsModal").find("[name=settings-statecheck]").each(function() {
        $(this).prop("checked", false)
      })
      $("#settingsModal").find("#settings-state-WA").prop("checked", true)
    } else if (data["data"]["which-state-version"] == "NT") {
      $("#settingsModal").find("[name=settings-statecheck]").each(function() {
        $(this).prop("checked", false)
      })
      $("#settingsModal").find("#settings-state-NT").prop("checked", true)
    }
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
    // Doesn't validate employee name.
    let employeename = $("#"+modalID).find("#employee-name-input").val().trim()
    // Doesn't validate which state
    let stateVersion = $("#"+modalID).find("[name=settings-statecheck]:checked").attr("contentz")

    if (abort) {return 0}

    $.when($.ajax({
    url: "http://localhost:8000/api/settings",
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      "wage-base-rate":wage,
      "usual-hours":usualhours,
      "employee-name":employeename,
      "which-state-version":stateVersion
    }),
    timeout: 4000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
      $("#navbarTitle").text("PayCAT-"+stateVersion)
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

function exportData() {
  let selectedID;
  if (selectedSidebarEntry != null) {
      selectedID = parseInt(selectedSidebarEntry.replace("-entry", ""))
  } else {
    alert("Select a study in order to export it.")
    return 0;
  }

  $.when($.ajax({
    url: "http://localhost:8000/api/studydata",
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      "mode":"export",
      "exportID":selectedID
    }),
    timeout: 10000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })).done(function (data) {
    alert("File saved successfully.")
  }).fail(function(jqXHR, textStatus, errorThrown) {
    if (!(errorThrown === "REQUEST TIMEOUT")) { //This 408 code thrown when user cancels the save dialogue
      alert(jqXHR["responseJSON"]["message"])
    }
  });
}

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}

function exportPDF() {
  //Collapse the sidebar
  if ($("#side-bar-collapse").hasClass("show")) {
    $("#button-toggle-sidebar").click()
  }
  //Expand all entries
  $("#content-column").find("[name=expandAllButton]").click()
  //Wait for animations
  delay(700).then(() => window.print());
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
    if (data["data"]["wage-base-rate"] == null || data["data"]["usual-hours"] == null || data["data"]["employee-name"] == null || data["data"]["which-state-version"] == null) { //If user needs to set default settings.
      validSettings = false;
    } else {
      validSettings = true;
      $("#navbarTitle").text("PayCAT-"+data["data"]["which-state-version"])
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
      //Unfortunately requires renaming of the labels and radio buttons also.
      $("#settingsModalFirstTime").find("#settings-state-WA").attr("id", "settings-state-WA-FT")
      $("#settingsModalFirstTime").find("[for=settings-state-WA]").attr("for", "settings-state-WA-FT")
      $("#settingsModalFirstTime").find("#settings-state-NT").attr("id", "settings-state-NT-FT")
      $("#settingsModalFirstTime").find("[for=settings-state-NT]").attr("for", "settings-state-NT-FT")
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
  }).fail(function (data) {
    alert("Unable to load configuration from server. Message: "+data["message"]);
  });

}

confirmSettingsNotUnset()

