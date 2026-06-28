/*=========================================
        MANUFACTURING ERP DASHBOARD
=========================================*/

document.addEventListener("DOMContentLoaded", function () {

    startClock();
    setGreeting();

    animateCounter("salesCounter", 245600, "₹ ");
    animateCounter("purchaseCounter", 152800, "₹ ");
    animateCounter("profitCounter", 92800, "₹ ");

    loadSalesChart();
    loadStockChart();

    floatingButton();

});


/*=========================================
        LIVE CLOCK
=========================================*/

function startClock(){

    const dateElement=document.getElementById("todayDate");
    const clockElement=document.getElementById("liveClock");

    function update(){

        const now=new Date();

        dateElement.innerHTML=now.toLocaleDateString(
            "en-IN",
            {
                weekday:"long",
                year:"numeric",
                month:"long",
                day:"numeric"
            }
        );

        clockElement.innerHTML=now.toLocaleTimeString(
            "en-IN"
        );

    }

    update();

    setInterval(update,1000);

}


/*=========================================
        GREETING
=========================================*/

function setGreeting(){

    const hour=new Date().getHours();

    let greet="Good Evening";

    if(hour<12){

        greet="Good Morning";

    }
    else if(hour<17){

        greet="Good Afternoon";

    }

    const heading=document.querySelector(".welcome-left h2");

    if(heading){

        heading.innerHTML=greet+", Administrator 👋";

    }

}


/*=========================================
        COUNTER ANIMATION
=========================================*/

function animateCounter(id,target,prefix=""){

    const element=document.getElementById(id);

    if(!element) return;

    let current=0;

    const step=Math.ceil(target/120);

    const timer=setInterval(()=>{

        current+=step;

        if(current>=target){

            current=target;

            clearInterval(timer);

        }

        element.innerHTML=
            prefix+
            current.toLocaleString("en-IN");

    },15);

}


/*=========================================
        SALES CHART
=========================================*/

function loadSalesChart(){

    const canvas=document.getElementById("salesChart");

    if(!canvas) return;

    new Chart(canvas,{

        type:"line",

        data:{

            labels:[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul"
            ],

            datasets:[{

                label:"Sales",

                data:[
                    20,
                    28,
                    35,
                    42,
                    55,
                    61,
                    74
                ],

                borderColor:"#2563eb",

                backgroundColor:"rgba(37,99,235,.15)",

                fill:true,

                tension:.4

            }]

        },

        options:{

            responsive:true,

            plugins:{

                legend:{
                    display:false
                }

            }

        }

    });

}


/*=========================================
        INVENTORY CHART
=========================================*/

function loadStockChart(){

    const canvas=document.getElementById("stockChart");

    if(!canvas) return;

    new Chart(canvas,{

        type:"doughnut",

        data:{

            labels:[
                "Raw Material",
                "Finished",
                "Waste"
            ],

            datasets:[{

                data:[
                    55,
                    35,
                    10
                ],

                backgroundColor:[

                    "#2563eb",
                    "#10b981",
                    "#ef4444"

                ]

            }]

        },

        options:{

            responsive:true,

            plugins:{

                legend:{
                    position:"bottom"
                }

            }

        }

    });

}


/*=========================================
        FLOATING BUTTON
=========================================*/

function floatingButton(){

    const fab=document.querySelector(".fab-button");

    if(!fab) return;

    fab.addEventListener("click",function(){

        alert(
            "Quick Menu\n\nPurchase\nSales\nProduction\nExpense"
        );

    });

}


/*=========================================
        AUTO REFRESH PLACEHOLDER
=========================================*/

setInterval(function(){

    console.log("Dashboard refreshed...");

},60000);