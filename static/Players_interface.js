// function drawing the life of the player in function of the radius of his ball
function drawLife(rayon)
{
  // h,v the x,y coordinates of the center of the life bar
  var h = 100;
  var v = 100;
  // radius of the life bar
  var r = 50;
  var diff;
  var arrondi;

  var vie = (rayon/15)*100;
  // base life : rayon = 15 if more because of the bonus, the circle stay fully green
  if(rayon > 15){
    diff = Math.PI*2;
  }
  else{
    diff = (vie/100)*Math.PI*2;
  }

  // drawing a withe circle for the background
  players_ctx.beginPath();
  players_ctx.arc(v,h,r,0,2*Math.PI,false);  // cercle blanc intérieur
  players_ctx.fillStyle='#FFF';
  players_ctx.fill();
  players_ctx.closePath();

  // drawing the green arc representing the life of the player
  players_ctx.beginPath();  // arc vert
  players_ctx.lineWidth = 15;
  players_ctx.strokeStyle = "#b3cf3c";
  players_ctx.arc(v,h,r,-Math.PI/2,-Math.PI/2+diff,false);
  players_ctx.stroke();
  players_ctx.closePath();

  // drawing the red arc representing the life lost
  players_ctx.beginPath();  // arc rouge
  players_ctx.strokeStyle = "#ea1f1f";
  players_ctx.arc(v,h,r,diff-Math.PI/2,3*Math.PI/2,false);
  players_ctx.stroke();
  players_ctx.closePath();

  // writing the % of the life in the middle of the life bar
  players_ctx.beginPath();
  players_ctx.fillStyle='#000';   // texte intérieur
  players_ctx.textAlign='center';
  players_ctx.font = '10pt Verdana'
  arrondi = Math.round(100*vie)/100;
  players_ctx.fillText(arrondi+'%',h+2,v+6);
  players_ctx.closePath();
}

// function drawing the ennemies positions on the minimap, (x,y) ennemy position, (w,h) position of the top left corner of the minimap
function drawPixel(x,y,w,h,color)
{
  // calculating the position on the minimap in function of the compressing rate of the minimap ( here 159/1327)
  var x_p = w + x*149/819;
  var y_p = h + y*148/818;

  // drawing the pixel
  players_ctx.beginPath();
  players_ctx.fillStyle = color;
  players_ctx.arc(x_p,y_p,3,0,2*Math.PI);
  players_ctx.fill();
  players_ctx.closePath();
}

// drawing the minimap
function drawMiniMap(logs){
  //(x,y) position of the top left corner of the minimap
  var x = players_canvas.width-170;
  var y = players_canvas.height-170;

  // chargin the image
  var img = new Image();
  img.src = "img_mini.png";
  // width and height  of the picture of the minimap
  var w = 149;
  var h = 148;

  // drawing a white rectangle for the background
  players_ctx.beginPath();
  players_ctx.fillStyle = "#FFF";
  players_ctx.fillRect(x,y,w,h);
  players_ctx.closePath();

  // drawing a border for the minimap
  players_ctx.beginPath();
  players_ctx.strokeStyle = "#d35400";
  players_ctx.lineWidth = 3;
  players_ctx.rect(x,y,w,h);
  players_ctx.stroke();
  players_ctx.closePath();

  // charging the minimap by its id defined in client.html
  var img = document.getElementById("source");
  players_ctx.drawImage(img,x,y);


  // drawing the players on the minimap
  for (var id_players in logs.client_players){
    if (id_players != logs.id){
      // enemies in red
      if(logs.client_players[id_players]["team"] == logs.client_players[logs.id]["team"]){
        drawPixel(logs.client_players[id_players]["x"],logs.client_players[id_players]["y"],x,y,"#01DF01");
      }
      // allies in green
      else{
        drawPixel(logs.client_players[id_players]["x"],logs.client_players[id_players]["y"],x,y,"#FF0000");
      }
    }
    // player himself in blue
    else{
      drawPixel(logs.client_players[id_players]["x"],logs.client_players[id_players]["y"],x,y,"#0000FF");
    }
  }
}

//function writing the pseudo of the players near their ball, (x,y) position of the ennemy on the canvas
function drawPseudo(logs,id_players)
{
  var pseudo = logs.client_players[id_players]["pseudo"];
  var x_ = logs.client_players[id_players]["x"] - logs.personalX + canvas_width/2;
  var y_ = logs.client_players[id_players]["y"] - logs.personalY + canvas_height/2-20;

  players_ctx.beginPath();
  players_ctx.font = "20px Arial";
  players_ctx.fillStyle = "#da6210";
  players_ctx.fillText(pseudo,x_,y_);
  players_ctx.closePath();
}

//function writing the 3 best scores
function drawScore(logs)
{
  // (x,y) positon on the canvas
  var x = 50;
  var y = players_canvas.height-100;
  // defining a table of existing id
  var id_best_score = [-1,-1,-1];
  var best_score =[-1,-1,-1];

  // calculating the 3 best score and updating the table id_best_score which contains the id of the 3 best players
  for (var idp in logs.client_players)
  {
<<<<<<< HEAD:ASSOS.io/static/Players_interface.js
    if(client_players[idp]["score"]>best_score[0]){
=======
    if( logs.client_players[idp]["score"] > best_score[0] )
    {
>>>>>>> f86aa21e0d5cc8cac739f5846c820391f7b51551:static/Players_interface.js
      id_best_score[2] = id_best_score[1];
      best_score[2] = best_score[1];
      id_best_score[1] = id_best_score[0];
      best_score[1] = best_score[0];
      id_best_score[0] = idp;
<<<<<<< HEAD:ASSOS.io/static/Players_interface.js
      best_score[0] = client_players[idp]["score"];

    }
    else if(client_players[idp]["score"]>best_score[1]){
      id_best_score[2] = id_best_score[1];
      best_score[2] = best_score[1];
      id_best_score[1] = idp;
      best_score[1] = client_players[idp]["score"];
    }
    else if(client_players[idp]["score"]>best_score[2]){
      id_best_score[2] = idp;
      best_score[2] = client_players[idp]["score"];
=======
      best_score[0] = logs.client_players[idp]["score"];

    }
    else if(logs.client_players[idp]["score"]>best_score[1]){
      id_best_score[2] = id_best_score[1];
      best_score[2] = best_score[1];
      id_best_score[1] = idp;
      best_score[1] = logs.client_players[idp]["score"];
    }
    else if(logs.client_players[idp]["score"]>best_score[2]){
      id_best_score[2] = idp;
      best_score[2] = logs.client_players[idp]["score"];
>>>>>>> f86aa21e0d5cc8cac739f5846c820391f7b51551:static/Players_interface.js
    }
  }

  // writing a title
  players_ctx.beginPath();
  players_ctx.font = "30px Arial";
  players_ctx.fillStyle = "#0040FF";
  players_ctx.fillText("Top 3 Players:",x+50,y-40);
  players_ctx.closePath();

  console.log(id_best_score);
  // writing the best scores
  for (var idp in id_best_score)
  {
    if(id_best_score[idp] != -1){
      //score of the player
<<<<<<< HEAD:ASSOS.io/static/Players_interface.js
      var sc = client_players[id_best_score[idp]]["score"];
      // string we want to write
      var s = client_players[id_best_score[idp]]["pseudo"] +" : " + sc.toString();
=======
      var sc = logs.client_players[id_best_score[idp]]["score"];
      // string we want to write
      var s = logs.client_players[id_best_score[idp]]["pseudo"] +" : " + sc.toString();
>>>>>>> f86aa21e0d5cc8cac739f5846c820391f7b51551:static/Players_interface.js

      // wrting the score on the canvas
      players_ctx.beginPath();
      players_ctx.font = "20px Arial";
      players_ctx.fillStyle = "#da6210";
      players_ctx.fillText(s,x,y);
      players_ctx.closePath();
      //updating the position where the score is written
      y = y + 30;
    }
  }
}

function drawTeamScores(logs){
  var x = players_canvas.width/2 - 150;
  var y = 40;
  var sc_allies;
  var sc_ennemies;

  if(logs.client_players[logs.id]["team"] == "blue"){
    sc_allies = logs.score_blue;
    sc_ennemies = logs.score_red;
  }
  else{
    sc_allies = logs.score_red;
    sc_ennemies = logs.score_blue;
  }
  var rate;
  if(sc_allies + sc_ennemies == 0){
    rate = 0.5;
  }
  else{
    rate = sc_allies / (sc_ennemies + sc_allies);
  }

  players_ctx.beginPath();
  players_ctx.fillStyle = "#0000FF";
  players_ctx.fillRect(x,y,400*rate,40);
  players_ctx.closePath();

  players_ctx.beginPath();
  players_ctx.fillStyle = "#FF0000";
  players_ctx.fillRect(x+400*rate,y,400*(1-rate),40);
  players_ctx.closePath();

  players_ctx.beginPath();
  players_ctx.fillStyle = "#000000";
  players_ctx.moveTo(x+400*rate-20,y);
  players_ctx.lineTo(x+400*rate,y+15);
  players_ctx.lineTo(x+400*rate+20,y);
  players_ctx.fill();
  players_ctx.closePath();

  players_ctx.beginPath();
  players_ctx.font = "30px Arial";
  players_ctx.fillStyle = "#000000";
  players_ctx.fillText(sc_allies.toString(),x-30,y+30);
  players_ctx.closePath();

  players_ctx.beginPath();
  players_ctx.font = "30px Arial";
  players_ctx.fillStyle = "#000000";
  players_ctx.fillText(sc_ennemies.toString(),x+400+25,y+30);
  players_ctx.closePath();

}

function drawWidgets(logs,id_players)
{
  drawPseudo(logs,id_players);
  drawMiniMap(logs);
  drawScore(logs);
  drawTeamScores(logs);
}
