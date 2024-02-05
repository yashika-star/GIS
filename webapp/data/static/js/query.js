var selectors = {
    tableBtn: ".table-btn",
    queryTextArea: "#sql",
    queryForm: "#data-query-form",
    uploadFileInput: "#upload-sql-file-input"
}
$(document).ready(function () {
    $(selectors.tableBtn).on("click", function () {
        var tablename = $(this).find("span:first").text();
        var sql = "SELECT * FROM " + tablename;
        $(selectors.queryTextArea).val(sql);
        $(selectors.queryForm).submit();
    });

    $(selectors.uploadFileInput).on("change", function () {
        var input = $(this)
        var file = input.prop("files")[0]
        fileDataAsText(file, function(data) {
            $(selectors.queryTextArea).val(data)
            input.val(null)
        })
    });
});

function fileDataAsText(file, cb) {
    var fileReader = new FileReader();
    fileReader.onload = function () {
        cb(fileReader.result)
    };
    fileReader.readAsText(file);
}