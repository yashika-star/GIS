var selectors = {
    fileType: "#file-type",
    file: "#file"
}
var fileTypeInfo = {
    geojson: {
        accpet: ".json,.geojson"
    },
    shp: {
        accpet: ".zip"
    },
    kml: {
        accpet: ".kml,.kmz"
    },
    kg: {
        accpet: "*"
    }
}
$(document).ready(function() {
    $(selectors.fileType).on("change", function(e) {
        var info = fileTypeInfo[e.target.value];
        $(selectors.file).attr("accept", info.accpet);
    });
});