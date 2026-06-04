import QtQuick
import QtQuick.Layouts

// Колонка из 5 карточек датчиков
Item {
    id: root
    property var sensors: []
    property var tokens: ({})

    ColumnLayout {
        anchors {
            fill: parent
            margins: 12
        }
        spacing: 10

        Repeater {
            model: root.sensors

            SensorCard {
                id: card
                Layout.fillWidth: true
                Layout.fillHeight: true

                sensorMeta: modelData || {id:"",short:"",full:"",unit:"",icon:"",color:"#888"}
                tokens: root.tokens

                // Обновление из bridge.sensorValues
                Connections {
                    target: bridge
                    function onSensorsUpdated() {
                        var list = bridge.sensorValues
                        for (var i = 0; i < list.length; i++) {
                            if (list[i].id === card.sensorMeta.id) {
                                card.displayValue = list[i].display
                                card.state        = list[i].state
                                break
                            }
                        }
                    }
                }

                onTapped: function(fullName) {
                    // Определяем сторону для позиции тоста
                    var gPos = card.mapToItem(root.parent, card.width / 2, card.height / 2)
                    var toastX = root.sensors === bridge.leftSensors
                                 ? 232 + 10
                                 : root.parent.width - 232 - 10 - 200
                    root.parent.showToast(fullName, toastX, gPos.y)
                }
            }
        }
    }
}
