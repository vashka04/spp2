<?php
// Comment

function calculateResult(int $value, array $items): int
{
    $sum = 0;
    $count = count($items);

//    if ($value < 0) {
//        $value = abs($value);
//    } elseif ($value === 0) {
//        $value = 1;
//    } else {
//        $value += 2;
//    }

//    for ($i = 0; $i < $count; $i++) {
//        if ($items[$i] > 10) {
//            $sum += $items[$i];
//        } else {
//            $sum++;
//        }
//    }

//    foreach ($items as $item) {
//        while ($item > 20) {
//            $item -= 5;
//            if ($item % 2 === 0) {
//                $sum += 2;
//            }
//        }
//    }

    $j = 0;
//    do {
//        $sum += $j;
//        $j++;
//    } while ($j < 3);

//    switch ($value) {
//        case 1:
//            $sum += 10;
//            break;
//        case 2:
//            $sum += 20;
//            break;
//        case 3:
//            $sum += 30;
//            break;
//        default:
//            $sum += 1;
//            break;
//    }

//    $status = ($sum > 100) ? 1 : 0;

//    if ($status === 1) {
//        if ($sum > 200) {
//            $sum = 200;
//        }
//    }

    return $sum;
}

$values = [3, 15, 25, 4, 100];
$result = calculateResult(2, $values);

//if ($result > 100) {
//    echo "Большой результат";
//} elseif ($result > 50) {
//    echo "Средний результат";
//} else {
//    echo "Небольшой результат";
//}

//for ($k = 0; $k < 2; $k++) {
//    echo $k;
//}
?>
