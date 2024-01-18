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

function newPDF() {
  $.when($.ajax({
      url: "http://localhost:8000/api/PDFData",
      type: 'POST',
      body: {},
      timeout: 180000, //3 minutes
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      updateSidebarList()
    }).fail(function (data) {
      alert("failed to add PDF.")
      //$('#card-container').html("<span class=\"fw-bold text-danger\">Failed to load PDF.</span>")
    });

}

//Refreshes the sidebar (which displays all payslips stored in the local shelf DB.)
function updateSidebarList() {
  //TODO:
  //AJAX call the local DB - GET /api/PDFData
  //jQuery - generate all list items after deleting all old ones.
  $.when($.ajax({
      url: "http://localhost:8000/api/PDFData",
      type: 'GET',
      body: {},
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      //Clear the sidebar by setting its contents to be only the header.
      $('#side-bar-listgroup').html($('#template-storage > #side-bar-header').clone().attr('id', 'side-bar-header-clone'))
      for (entryID in data["data"]) {
        //for each entry in the shelf database, create a new entry in the sidebar
        if (data["data"][entryID]["type"] == "view") {
          $('#side-bar-listgroup').append($('#template-storage > #side-bar-view').clone().attr('id',String(entryID)+"-entry"))
          $('#side-bar-listgroup').find('#'+String(entryID)+"-entry").find("#file-title").text(data["data"][entryID]["name"])
          $('#side-bar-listgroup').find('#'+String(entryID)+"-entry").find("#sbv-delbutton").attr('onclick', "deleteSidebarEntry("+entryID+"); event.stopPropagation();")
          $('#side-bar-listgroup').find('#'+String(entryID)+"-entry").attr('onclick', "selectSidebarEntry("+entryID+")")
        } else if (data["data"][entryID]["type"] == "compare") {
          alert("compare")
        }
        // Is selected?
        if (entryID+"-entry" == selectedSidebarEntry) {
          $('#side-bar-listgroup').find('#'+String(entryID)+"-entry").addClass("bg-primary-subtle")
        }
      }
    }).fail(function (data) {
      alert("Failed filling sidebar");
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
      url: "http://localhost:8000/api/PDFData/"+pdfID,
      type: 'GET',
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      // --- For VIEW-type entries: ---
      if (data["data"]["type"] == "view") {
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
      // --- For COMPARE-type entries: ---
      } else if (data["type"] == "compare") {
        alert("todo")
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
      url: "http://localhost:8000/api/PDFData/"+String(pdfID),
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

//When no payslip entry is selected, this is the data shown.
function displayNoSelection() {
  $('#content-column').html("")
  $('#content-column').html($('#template-storage > #noContent').clone().attr('id','noContent-clone'))

}