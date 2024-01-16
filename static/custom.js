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


function importPDFData() {
  $.when($.ajax({
      url: "http://localhost:8000/api/PDFData/test2.pdf",
      type: 'GET',
      timeout: 4000,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })).done(function (data) {
      for (date in data["data"]) {
        //Clone a new card, rename it's ID as the date, and remove hidden.
        $('#card-container').append($('#item-template').clone().removeAttr('hidden').attr("id", date+"-card"))
        //Uniqify the collapse IDs (generic)
        $('#'+date+"-card > .card-header").attr("href", "#"+date+"-collapse")
        $('#'+date+"-card > .collapse").attr("id", date+"-collapse")
        //Fill all the values in the card
        let sumAmount = 0
        $('#'+date+"-card").find("#item-date").text(date)       
        //Fill each item in a date entry
        for (let i = 0; i < data["data"][date].length; i++) {
          let entry = data["data"][date][i]
          sumAmount += parseFloat(entry["amount"])
          $('#'+date+"-card").find("#item-entry-container").append($('#'+date+"-card").find("#item-entry").clone().removeAttr('hidden').attr('id', "item-entry"+i))
          //Only if they're defined, fill units/rate
          if (typeof entry["units"] !== 'undefined') {
            $('#'+date+"-card").find("#item-entry"+i).find("#item-unitsrate").text("("+entry["units"] + "h @ $" + entry["rate"]+")")
          } else {
            $('#'+date+"-card").find("#item-entry"+i).find("#item-unitsrate").text("")            
          }
          //If units are negative, highlight this.
          if (entry["units"] < 0) {
            $('#'+date+"-card").find("#item-entry"+i).find("#item-unitsrate").addClass("text-danger-emphasis")
          }
          if (entry["amount"] < 0 ) {
            $('#'+date+"-card").find("#item-entry"+i).find("#item-amount").addClass("text-danger")
          }
          $('#'+date+"-card").find("#item-entry"+i).find("#item-description").text(entry["description"])
          $('#'+date+"-card").find("#item-entry"+i).find("#item-amount").text(entry["amount"])
        
        }
        //finally record the sum of all amounts
         $('#'+date+"-card").find("#item-total").text("$"+sumAmount.toFixed(2).toString())
      }

    }).fail(function (data) {
      alert("failed")
      $('#card-container').html("<span class=\"fw-bold text-danger\">Failed to load PDF.</span>")
    });

}

//Refreshes the sidebar (which displays all payslips stored in the local shelf DB.)
function updateSidebarList() {
  //TODO:
  //AJAX call the local DB - GET /api/PDFData
  //jQuery - generate all list items after deleting all old ones.
}

function deletePDFEntry(pdfNameShort) {
  //TODO:
  //AJAX call local DB - DELETE /api/PDFData/<file name.pdf>
}

//When no payslip entry is selected, this is the data shown.
function displayNoSelection() {
  //TODO:
  //jQuery - empty the main display window (delete all)
  //jQuery - clone the 'empty page' display.
}