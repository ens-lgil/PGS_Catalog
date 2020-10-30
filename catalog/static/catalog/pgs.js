$(document).ready(function() {


    // Fix issue with internal links because of the sticky header
    function offsetAnchor() {
      if(location.hash.length !== 0) {
        window.scrollTo(window.scrollX, window.scrollY - 95);
      }
    }
    // This will capture hash changes while on the page
    $(window).on("hashchange",offsetAnchor);
    // This is here so that when you enter the page with a hash,
    // it can provide the offset in that case too. Having a timeout
    // seems necessary to allow the browser to jump to the anchor first.
    window.setTimeout(offsetAnchor, 0.1);

    // Shorten content having long text
    shorten_displayed_content();

    $('body').on("click", 'span.morelink', function(){
        if($(this).hasClass("link_less")) {
          $(this).html(moretext);
        } else if ($(this).hasClass("link_more")){
          $(this).html(lesstext);
        }
        $(this).toggleClass("link_less link_more");
        // Show/hide "..." characters
        $(this).parent().find('.moreellipses').toggle();
        // Show/hide the rest of the text
        $(this).parent().find('.morecontent').toggle();
        return false;
    });

    // Add external link icon and taget blank for external links
    function alter_external_links(prefix) {
      if (!prefix) {
        prefix = '';
      }
      else {
        prefix += ' '
      }
      $(prefix+'a[href^="http"]').attr('target','_blank');
      $(prefix+'a[href^="http"]').not('[class*="pgs_no_icon_link"]').addClass("external-link");
    }
    alter_external_links();

    // Tooltip | Popover
    function pgs_tooltip() {
      $('.pgs_helptip').attr('data-toggle','tooltip').attr('data-placement','bottom').attr('data-delay','800');
      $('.pgs_helpover').attr('data-toggle','popover').attr('data-placement','bottom');

      $('[data-toggle="tooltip"]').tooltip();
      $('[data-toggle="popover"]').popover();
    }
    pgs_tooltip();

    // EMBL-EBI Data Protection banner
    var localFrameworkVersion = '1.3'; // 1.1 or 1.2 or compliance or other
    // if you select compliance or other we will add some helpful
    // CSS styling, but you may need to add some CSS yourself
    var newDataProtectionNotificationBanner = document.createElement('script');
    newDataProtectionNotificationBanner.src = 'https://ebi.emblstatic.net/web_guidelines/EBI-Framework/v'+localFrameworkVersion+'/js/ebi-global-includes/script/5_ebiFrameworkNotificationBanner.js?legacyRequest='+localFrameworkVersion;
    document.head.appendChild(newDataProtectionNotificationBanner);
    newDataProtectionNotificationBanner.onload = function() {
      ebiFrameworkRunDataProtectionBanner(localFrameworkVersion); // invoke the banner
    };

    function pgs_toggle_btn(el) {
      el.find('i').toggleClass("fa-plus-circle fa-minus-circle");
      id = el.attr('id');
      prefix = '#list_';
      $(prefix+id).toggle();
      if ($(prefix+id).is(":visible")) {
        fadeIn($(prefix+id));
      }
    }

    // Button toggle
    $('.toggle_btn').click(function() {
      pgs_toggle_btn($(this));
    });
    // Button toggle within an HTML table
    $('table.table[data-toggle="table"]').on("click", ".toggle_table_btn", function(){
      pgs_tooltip();
      pgs_toggle_btn($(this));
    });

    // Shorten long text in table after each sorting or filtering of the table
    // This is due to the bootstrap-table library rebuilding the table content at each sorting/filtering
    // Shorten long text in table after each sorting or filtering of the table
    // This is due to the bootstrap-table library rebuilding the table content at each sorting/filtering

    // Run the "post processing" once the tables have been loaded and sorted by default
    $('table.table[data-toggle="table"]').each(function(){
      // Remove column search if the number of rows is too small
      var trs = $( this ).find( "tbody > tr");
      if (trs.length < 3) {
        $( this ).find('.fht-cell').hide()
      }
      // Alter the table display
      setTimeout(function(){
        alter_external_links('table.table[data-toggle="table"] tbody');
        pgs_tooltip();
        shorten_displayed_content();
      }, 500);
    });

    // Run the "post processing" after a manual sorting
    $('table.table[data-toggle="table"]').on("click", ".sortable", function(){
      setTimeout(function(){
        alter_external_links('table.table[data-toggle="table"] tbody');
        pgs_tooltip();
        shorten_displayed_content();
      }, 0);
    });
    // Run the "post processing" after a manual filtering
    var timer;
    $('.form-control').keyup(function(){
      clearTimeout(timer);
      if ($('.form-control').val) {
          timer = setTimeout(function(){
            alter_external_links('table.table[data-toggle="table"] tbody');
            pgs_tooltip();
            shorten_displayed_content();
          }, 1000);
      }
    });


    // Remove pagination text if there is no pagination links
    $('.fixed-table-pagination').each(function(index) {
      var page_list = $( this ).find('.page-list');
      if (page_list.length == 0) {
        $( this ).remove();
      }
      else {
        if (page_list.css('display') == 'none') {
          $( this ).remove();
        }
      }
    });

    // Update to the scientific notation (1x10-1 and 1e-1)
    if ($('#pgs_params').length) {
      var pgs_param = $('#pgs_params').html();
      var matches = pgs_param.match(/\d+(x10|e)(-?\d+)/);
      if (matches && matches.length > 2) {
        for(var i=2; i<matches.length; i++) {
          if (matches[i] == 'x10' || matches[i] == 'e') {
            continue;
          }
          var chars = (matches[i-1] == 'x10') ? 'x10' : 'e';
          var pgs_param_sup = pgs_param.replace(chars+matches[i], chars+"<sup>"+matches[i]+"</sup>");
          $('#pgs_params').html(pgs_param_sup);
          pgs_param = pgs_param_sup;
        }
      }
      // Update rsquare notation (r2)
      $('#pgs_params').html(pgs_param.replace("r2", "r<sup>2</sup>"));
    }


    $('.pgs-ftp-btn').hover(function() {
      $(this).children('span').toggleClass('fa-folder fa-folder-open');
    });

    $('body').on("click", '#include_children', function(){
      console.log("Clicked!");
      if ($(this).prop("checked") == true) {
        $(location).attr('href','/trait/'+$(this).val());
      }
      else {
        $(location).attr('href','/trait/'+$(this).val()+'?include_children=false');
      }
    });

    // Control on search form(s)
    $('#search_btn').click(function() {
      console.log("Clicked");
      if ($('#q').val() && $('#q').val() != ''){
        $('#search_form').submit();
      }
    })
    $('#search_btn_2').click(function() {
      console.log("Clicked");
      if ($('#q2').val() && $('#q2').val() != ''){
        $('#search_form_2').submit();
      }
    })

    // Load google from iframe
    $('#g_iframe').on("load", function () {
      $('#iframe_loading').removeClass('d-flex');
      $('#iframe_loading').css('display', 'none');
    });


    // Add the following code if you want the name of the file appear on select
    $(".custom-file-input").on("change", function() {
      console.log("YES");
      var fileName = $(this).val().split("\\").pop();
      console.log(fileName);
      $(this).siblings(".custom-file-label").addClass("selected").html(fileName);

      fileExt = fileName.split("\.").pop();
      console.log(fileExt);
      if (fileExt != 'xlsx') {
        $('#error_file_extension').show();
        $('#upload_btn').hide();
        $('#upload_btn').removeAttr('type');
      }
      else {
        $('#error_file_extension').hide();
        $('#upload_btn').attr('type', 'submit');
        $('#upload_btn').show();
      }

    });


    /*$('.trait_item').mouseover(function(d) {
      var id = $(this).attr('id');
      var id_path = id.replace("_id", "");
      current_color = d3.select("path[data-id='"+id_path+"']").style("fill");
      d3.select("path[data-id='"+id_path+"']")
        .attr("d", arcOver)
        .attr("fill", d3.hsl(current_color).darker(0.5));
    });
    $('.trait_item').mouseout(function(d) {
      var id = $(this).attr('id');
      var id_path = id.replace("_id", "");
      current_color = d3.select("path[data-id='"+id_path+"']").style("fill");
      d3.select("path[data-id='"+id_path+"']")
        .attr("d", arc)
        .attr("fill", d3.hsl(current_color).brighter(0.5));
    });*/
});




function search_validator(){
   if($('#q').val()){
      $('#search_form').submit();
      return(true);
   }
   else {
      return(false);
   }
}

/*
 * Function to shorten content having long text
 */
var showChar = 100;  // How many characters are shown by default
var ellipsestext = "...";
var moretext = 'Show more';
var lesstext = 'Show less';

function shorten_displayed_content() {
  $('.more').each(function() {
      var content = $(this).html();
      if (content.length > showChar ){
        if (content.search('.moreellipses') == -1) {
          var c = content.substr(0, showChar);
          var h = content.substr(showChar, content.length - showChar);
          var html = c + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span><span class="morecontent">' + h + '</span><span class="morelink link_more">' + moretext + '</span>';
          $(this).html(html);
        }
      }
  });
}



/*
 * Functions to display the trait category piechart and the different trait
 * categories and traits boxes.
 */

function reset_showhide_trait() {
  // Reset traits
  $('.trait_subcat_container').hide("slow");
  // Reset container min width (for horizontal scrolling)
  $('.trait_cat_container').css('min-width', '300px');
  // Reset button
  $('#reset_cat').hide("slow");
  // Reset search
  add_search_term('');
}

function fadeIn(elem) {
  elem.css('opacity', 0);
  elem.css('display', 'block');

  var op = 0.1;  // opacity step

  // Fade in the elem (fadeIn() is not included in the slim version of jQuery)
  var timer = setInterval(function () {
    if (op >= 1){
      clearInterval(timer);
    }
    elem.css('opacity', op);
    elem.css('filter', 'alpha(opacity=' + op * 100 + ")");
    op += op * 0.1;
  }, 15);
}

function showhide_trait(id, term) {
  var elem = $('#'+id);

  if (!elem.is(':visible')) {
    // Hide previously selected traits
    $('.trait_subcat_container').hide();

    // Display list of traits
    fadeIn(elem);

    // Add search term to filter the table
    add_search_term(term);

    // Change the min width to avoid having the lists under each other.
    // Trigger an horinzontal scroll
    $('.trait_cat_container').css('min-width', '800px');

    // Reset button
    $('#reset_cat').show("slow");
  }

  $('a.trait_item').mouseover(function() {
    trait_link = $(this).find('.trait_link');
    if (trait_link.length == 0) {
      $(this).append('<i class="trait_link fa fa-link"></i>');
    }
    else {
      trait_link.show();
    }
  });
  $('a.trait_item').mouseout(function() {
    $(this).find('.trait_link').hide();
  });
}


function add_search_term(term) {

  var elems = $('.search-input');
  if (elems.length > 0) {
    elem = elems[0];
    elem.focus({preventScroll: true});
    elem.value = term;
    elem.blur();

    setTimeout(function(){
      $('table.table[data-toggle="table"] tbody a[href^="http"]').attr('target','_blank');
      $('table.table[data-toggle="table"] tbody a[href^="http"]').not('[class*="pgs_no_icon_link"]').addClass("external-link");
    }, 500);
  }
}


// Buttons in the Search page results
$('.search_facet').click(function(){
  if ($(this).find('i.fa-circle-o')) {
    id = $(this).attr('id');
    type = id.replace('_facet', '');
    if (type == 'all') {
      $('.pgs_result').show();
    }
    else {
      entry_class = type+'_entry';
      $('.'+entry_class).show();
      $('.pgs_result').not('.'+entry_class).hide();
    }
    title = type.charAt(0).toUpperCase() + type.slice(1);

    $('.search_facet.selected').find('i').removeClass("fa-check-circle").addClass("fa-circle-o");
    $('.search_facet.selected').removeClass("selected");

    $(this).find('i').removeClass("fa-circle-o").addClass("fa-check-circle");
    $(this).addClass("selected");
  }
});


// Build and draw the Trait category piechart
/*function draw_trait_category_piechart(data_chart) {

  var labels_list = [];
  var bg_list = [];
  var count_list = [];

  $.each(data_chart, function(index, data) {
    labels_list.push(data.name);
    bg_list.push(data.colour);
    count_list.push(data.size_g);
  });

  var chart_element = document.getElementById("trait_cat_piechart");
  new Chart(chart_element, {
    type: 'doughnut',
    data: {
      labels: labels_list,
      datasets: [{
        label: "PGS Scores per trait category",
        backgroundColor: bg_list,
        data: count_list
      }]
    },
    options: {
      title: {
        display: false
      },
      legend: {
        display: false
      },
      responsive: true,
      'onClick' : function (evt, item) {
        if (item[0]) {
          var index = item[0]['_index'];
          showhide_trait(data_chart[index].id+"_list", labels_list[index]);

        }
      },
      hover: {
        onHover: function(e, el) {
          $("#trait_cat_piechart").css("cursor", el[0] ? "pointer" : "default");
        }
      }
    }
  });
}*/


function display_category_list(data_json) {
  var trait_elem = document.getElementById("trait_cat");
  var subtrait_elem = document.getElementById("trait_subcat");

  item_height = 35;
  number_of_cat = Object.keys(data_json).length;

  cat_div_height = number_of_cat * item_height;
  cat_div_height += 'px';

  category_tooltip = 'data-toggle="tooltip" title=""';
  colour_to_replace = '##COLOUR##';
  colour_box = '<span class="trait_colour" style="background-color:'+colour_to_replace+'"></span>';
  count_to_replace = '##COUNT##';
  count_badge = '<span class="badge badge-pill badge-pgs float_right">'+count_to_replace+' <span>PGS</span></span>';
  category_arrow = '<i class="fa fa-arrow-circle-right"></i>';

  for (cat_index in data_json) {
    cat_index = parseInt(cat_index);

    var name     = data_json[cat_index].name;
    var cat_id   = data_json[cat_index].id+"_id";
    var div_id   = data_json[cat_index].id+"_list";
    var t_colour = data_json[cat_index].colour;
    var size_g   = data_json[cat_index].size_g;

    // Get an idea if the colour is quite light. If so, it will outline the arrow
    colour_light = t_colour.match(/^#(\w)\w(\w)\w(\w)/);
    count_nb_f = 0
    for (var i=1;i<4;i++) {
      if (colour_light[i] == 'F' || colour_light[i] == 'f') {
        count_nb_f++;
      }
    }

    var colour_span = colour_box.replace(colour_to_replace,t_colour);
    if (count_nb_f > 1) {
      colour_span = colour_span.replace('trait_colour','trait_colour trait_colour_border');
    }

    // Create category box
    var e = document.createElement('div');
    e.className = "trait_item";
    e.innerHTML = colour_span+'<span>'+name+'</span>'+count_badge.replace(count_to_replace,size_g);
    e.id = cat_id;
    e.setAttribute("data-toggle", "tooltip");
    e.setAttribute("data-placement", "left");
    e.setAttribute("data-delay", "800");
    e.setAttribute("title", "Click to display the list of traits related to '"+name+"'");
    e.setAttribute("onclick", "showhide_trait('"+div_id+"', '"+name+"')");
    trait_elem.appendChild(e);


    // Create sub-categories (traits) main container
    subcat_children = data_json[cat_index].children;
    var se = document.createElement('div');
    se.id = div_id;
    se.className = "trait_subcat_container clearfix";
    se.style.display = "none";

    // Arrow separator - vertical position
    var se_left = document.createElement('div');
    var class_name = (count_nb_f>1) ? 'trait_subcat_left trait_subcat_border' : 'trait_subcat_left';
    se_left.className = class_name;
    se_left.style.color = t_colour;
    se_left.innerHTML = category_arrow;
    var subcat_div_height_left = cat_index * item_height - 1;
    se_left.style.marginTop = subcat_div_height_left+"px";
    se.appendChild(se_left);

    // Sub-categories (traits) sub container - vertical position
    var se_right = document.createElement('div');
    se_right.className = "trait_subcat_right";

    var subcat_div_height_right = 0;
    var count = cat_index + (subcat_children.length/2);

    // One sub-category entry
    if (subcat_children.length == 1) {
      subcat_div_height_right = cat_index * item_height;
    }
    // Last entry
    else if (cat_index == number_of_cat-1) {
      cat_pos = cat_index * item_height;
      if (subcat_children.length < number_of_cat) {
        subcat_div_height_right = (number_of_cat - subcat_children.length)*item_height;
      }
    }
    // Other entries with more than 1 sub-category
    else if ((cat_index + (subcat_children.length/2)) < number_of_cat) {
      cat_pos = cat_index * item_height;
      subcat_div_height_right = cat_pos - ((subcat_children.length)*item_height)/2 + item_height/2;
    }
    // Other entries with more than 1 sub-category going over the end of the list
    else if ((cat_index + (subcat_children.length/2)) >= number_of_cat && subcat_children.length <= number_of_cat) {
      cat_pos = cat_index * item_height;
      subcat_div_height_right = (number_of_cat - subcat_children.length)*item_height;
    }

    // Display scrollbar for categories with lots of traits
    if (subcat_children.length > number_of_cat) {
      se_right.style.maxHeight = cat_div_height;
      se_right.classList.add("v-scroll");
    }

    se_right.style.marginTop = subcat_div_height_right+"px";

    // Create the sub-categories (traits) boxes
    for (subcat_index in subcat_children) {
      var sc_id   = subcat_children[subcat_index].id;
      var sc_name = subcat_children[subcat_index].name;
      var sc_size = subcat_children[subcat_index].size;
      var sc = document.createElement('a');
      sc.className = "trait_item";
      sc.innerHTML = colour_span+'<span>'+sc_name+'</span>'+count_badge.replace(count_to_replace,sc_size);
      sc.setAttribute("href", "/trait/"+sc_id);
      sc.setAttribute("data-toggle", "tooltip");
      sc.setAttribute("data-placement", "left");
      sc.setAttribute("data-delay", "800");
      sc.setAttribute("title", "Click to go to the detailed page of the '"+sc_name+"' trait");
      se_right.appendChild(sc);
    }
    se.appendChild(se_right);

    subtrait_elem.appendChild(se);
  }

  // Display list of trait categories
  fadeIn($("#trait_cat"));
}


// Build and draw sample distribution piecharts
/*function draw_samples_piechart(data_chart, id, type) {

  var pc_class   = (type == 'sample') ? "sample_piechart_" : "sample_piechart_gender_";
  var pc_colours = (type == 'sample') ? ["#3e95cd", "#8e5ea2"] : ["#F18F2B", "#4F78A7"];
  var pc_title   = (type == 'sample') ? 'Sample distribution' : 'Sample gender distribution';

  new Chart(document.getElementById(pc_class+id), {
    type: 'doughnut',
    data: {
      labels: data_chart[0],
      datasets: [{
        backgroundColor: pc_colours,
        data: data_chart[1]
      }]
    },
    options: {
      title: {
        display: true,
        text: pc_title
      },
      legend: {
        position: 'bottom',
        reverse: true,
        labels: {
          boxWidth: 20
        }
      }
    }
  });
}*/

//----------------------//
//  D3 chart functions  //
//----------------------//

// Return a D3 arc object
function get_d3_arc(radius,inner_coef, outer_coef) {
    if (!outer_coef) {
      outer_coef = 1;
    }
   return d3.arc().innerRadius(radius * inner_coef).outerRadius(radius * outer_coef);
}

// Add a Bootstrap tooltip to the D3 chart
function add_tooltip(elem, title) {
  elem.tooltip({
    'title': title,
    'placement': 'right',
    'html': true
  });
}


// Build and draw the Trait category piechart
function draw_trait_category_piechart(data) {

  var height = 260;
  var width = 300;

  var color = d3.scaleOrdinal()
    .domain(data.map(d => d.name))
    .range(data.map(d => d.colour))

  var margin = 10;
  var radius = Math.min(width, height - margin) / 2;

  var arc = get_d3_arc(radius, 0.55);

  var arcOver = get_d3_arc(radius, 0.53, 1.02);

  var pie = d3.pie()
    .padAngle(0.01)
    .sort(null) // Do not sort group by size
    .value(d => d.size_g)

  var arcs = pie(data);

  var svg = d3.select("#trait_cat_piechart")
    .attr("width", width)
    .attr("height", height);

  var g = svg.append("g")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

  g.selectAll("path")
    .data(arcs)
    .join("path")
      .attr("fill", d => color(d.data.name))
      .attr("d", arc)
      .attr("cursor", "pointer")
      .attr("data-label", d => d.data.name)
      .attr("data-id", d => d.data.id)
      // Tooltip
      .each(function(d,i){
        var title = '<b>'+d.data.name +"</b>: "+d.data.size_g+" PGS";
        add_tooltip($(this), title);
      })
      .on("click", function(d,i){
          var label = $(this).attr('data-label');
          var id = $(this).attr('data-id');
          showhide_trait(id+"_list", label);
      })
      .on("mouseover", function(d) {
        current_color = d3.select(this).style("fill");
        d3.select(this)
          .attr("d", arcOver)
          .attr("fill", d3.hsl(current_color).darker(0.5));
        var id = $(this).attr('data-id');
        $('#'+id+"_id").addClass('trait_item_selected');
        $('#'+id+"_id").removeClass('trait_item');

      })
      .on("mouseout", function(d) {
        current_color = d3.select(this).style("fill");
        d3.select(this)
          .attr("d", arc)
          .attr("fill", d3.hsl(current_color).brighter(0.5));
          var id = $(this).attr('data-id');
          $('#'+id+"_id").addClass('trait_item');
          $('#'+id+"_id").removeClass('trait_item_selected');
      });
}


// Build and draw sample distribution piecharts
function draw_samples_piechart(data, id, type) {

  var pc_svg_id  = (type == 'sample') ? "sample_piechart_"+id : "sample_piechart_gender_"+id;
  var pc_colours = (type == 'sample') ? ["#3e95cd", "#8e5ea2"] : ["#F18F2B", "#4F78A7"];

  var height = 160;
  var width = 200;
  var margin = 60;

  var color = d3.scaleOrdinal()
    .domain(data.map(d => d.name))
    .range(pc_colours)

  var radius = Math.min(width, height - margin) / 2;

  var arc = get_d3_arc(radius, 0.58);

  var arcOver = get_d3_arc(radius, 0.56, 1.02);

  var pie = d3.pie()
    .padAngle(0.025)
    .sort(null) // Do not sort group by size
    .value(d => d.value)

  var arcs = pie(data);

  var svg = d3.select("#"+pc_svg_id)
    .attr("width", width)
    .attr("height", height);

  var g = svg.append("g")
    .attr("transform", "translate(" + width / 2 + "," + ((height - (margin - 20)) / 2) + ")");

  g.selectAll("path")
    .data(arcs)
    .join("path")
      .attr("fill", d => color(d.data.name))
      .each(function(d,i){
        var title = '<b>'+d.data.name +"</b>: "+d.data.value;
        add_tooltip($(this), title);
      })
      .on("mouseover", function(d) {
        current_color = d3.select(this).style("fill");
        d3.select(this)
          .attr("d", arcOver)
          .attr("fill", d3.hsl(current_color).darker(0.5));
      })
      .on("mouseout", function(d) {
        current_color = d3.select(this).style("fill");
        d3.select(this)
          .attr("d", arc)
          .attr("fill", d3.hsl(current_color).brighter(0.5));
      })
      .transition()
        .duration(500)
        .attrTween('d', function(d) {
          var i = d3.interpolate(d.startAngle+0.1, d.endAngle);
          return function(t) {
            d.endAngle = i(t);
            return arc(d);
          }
        });

  // Legend
  var rect_width = 20;
  var rect_height = 14;

  // Reverse orders to match the piechart display
  data_legend = data;
  data_legend.reverse()

  var pc_colours_legend = pc_colours;
  pc_colours_legend.reverse()

  var color_legend = d3.scaleOrdinal()
    .domain(data_legend.map(d => d.name))
    .range(pc_colours_legend)

  var nodeWidth = (d) => d.getBBox().width;

  // Create D3 legend
  const legend = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', 'translate(0,0)');

  const lg = legend.selectAll('g')
    .data(data_legend)
    .enter()
    .append('g')
      .attr('transform', (d,i) => `translate(${i * 100},${height/2 + 15})`);

  lg.append('rect')
    .style('fill', d => color_legend(d.value))
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', rect_width)
    .attr('height', rect_height);

  lg.append('text')
    .style('font-size', rect_height - 2)
    .style('fill', '#555')
    .attr('x', rect_width + 5)
    .attr('y', rect_height - 3)
    .text(d => d.name);

  var offset = 0;
  lg.attr('transform', function(d, i) {
    var x = offset;
    offset += nodeWidth(this) + 10;
    return `translate(${x},${height - margin/2 - 4})`;
  });

  legend.attr('transform', function() {
    return `translate(${(width - nodeWidth(this)) / 2},${0})`
  });
}
