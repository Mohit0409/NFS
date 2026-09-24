(function () {
  'use strict';

  const activityFactors = {
    sedentary: 1.2,
    light: 1.3,
    moderate: 1.4,
    active: 1.5
  };

  const gymDayAdjustments = { 0: 0, 2: 0.04, 4: 0.08, 6: 0.12, 7: 0.14 };
  const minimumBudgetByDiet = { vegetarian: 100, vegan: 110, eggetarian: 120, nonveg: 150 };

  const goalRules = {
    loss: { label: 'Fat-loss starting plan', calorieFactor: 0.85, proteinFactor: 1.7 },
    gain: { label: 'Muscle-building starting plan', calorieFactor: 1.08, proteinFactor: 1.7 },
    recomp: { label: 'Body-recomposition starting plan', calorieFactor: 0.95, proteinFactor: 1.7 },
    maintain: { label: 'Fitness-maintenance plan', calorieFactor: 1, proteinFactor: 1.5 }
  };

  const dietLabels = {
    vegetarian: 'Vegetarian',
    eggetarian: 'Eggetarian',
    nonveg: 'Non-vegetarian',
    vegan: 'Vegan'
  };

  const mealLibrary = {
    vegetarian: {
      booster: { name: 'Soya chunks protein top-up', quantity: 30, unit: 'g raw', calories: 103, protein: 16, carbs: 10, fat: 0.5, fibre: 4, cost: 6 },
      meals: [
        meal('Breakfast', 'Moong chilla, curd & banana', 560, 31, 92, 8, 16, 42, [food('Moong dal for chilla batter', 100, 'g raw'), food('Plain curd', 150, 'g'), food('Banana', 1, 'medium'), food('Vegetables in chilla', 100, 'g')]),
        meal('Lunch', 'Dal, roti, sabzi & salad', 710, 33, 125, 12, 24, 50, [food('Whole-wheat atta', 90, 'g raw'), food('Mixed dal', 70, 'g raw'), food('Seasonal vegetables', 200, 'g'), food('Fresh salad', 150, 'g'), food('Cooking oil', 5, 'ml')]),
        meal('Pre-workout snack', 'Roasted chana & seasonal fruit', 280, 13, 52, 4, 12, 17, [food('Roasted chana', 60, 'g'), food('Seasonal fruit', 150, 'g')]),
        meal('Recovery', 'Milk & peanuts', 265, 14, 21, 14, 2, 22, [food('Toned milk', 300, 'ml'), food('Peanuts', 15, 'g')]),
        meal('Dinner', 'Soya rice bowl with vegetables', 625, 42, 98, 10, 17, 39, [food('Soya chunks', 60, 'g raw'), food('Rice', 70, 'g raw'), food('Seasonal vegetables', 250, 'g'), food('Cooking oil', 5, 'ml')])
      ]
    },
    vegan: {
      booster: { name: 'Soya chunks protein top-up', quantity: 30, unit: 'g raw', calories: 103, protein: 16, carbs: 10, fat: 0.5, fibre: 4, cost: 6 },
      meals: [
        meal('Breakfast', 'Besan chilla, tofu & banana', 600, 31, 86, 17, 15, 55, [food('Besan', 100, 'g raw'), food('Tofu', 100, 'g'), food('Vegetables in chilla', 100, 'g'), food('Banana', 1, 'medium')]),
        meal('Lunch', 'Dal, roti, sabzi & salad', 750, 34, 128, 14, 25, 52, [food('Whole-wheat atta', 90, 'g raw'), food('Mixed dal', 80, 'g raw'), food('Seasonal vegetables', 200, 'g'), food('Fresh salad', 150, 'g'), food('Cooking oil', 7, 'ml')]),
        meal('Pre-workout snack', 'Roasted chana & guava', 320, 14, 57, 5, 15, 22, [food('Roasted chana', 60, 'g'), food('Guava or seasonal fruit', 150, 'g')]),
        meal('Recovery', 'Sprouts & peanuts', 300, 19, 35, 11, 12, 26, [food('Mixed sprouts', 200, 'g cooked'), food('Peanuts', 20, 'g'), food('Lemon and vegetables', 100, 'g')]),
        meal('Dinner', 'Soya rice bowl with vegetables', 670, 46, 101, 11, 18, 44, [food('Soya chunks', 70, 'g raw'), food('Rice', 70, 'g raw'), food('Seasonal vegetables', 250, 'g'), food('Cooking oil', 5, 'ml')])
      ]
    },
    eggetarian: {
      booster: { name: 'Soya chunks protein top-up', quantity: 30, unit: 'g raw', calories: 103, protein: 16, carbs: 10, fat: 0.5, fibre: 4, cost: 6 },
      meals: [
        meal('Breakfast', 'Egg bhurji & vegetable poha', 580, 29, 78, 19, 9, 48, [food('Whole eggs', 3, 'whole'), food('Poha', 80, 'g raw'), food('Mixed vegetables', 120, 'g'), food('Cooking oil', 5, 'ml')]),
        meal('Lunch', 'Dal, roti, curd, sabzi & salad', 760, 38, 126, 15, 24, 62, [food('Whole-wheat atta', 90, 'g raw'), food('Mixed dal', 70, 'g raw'), food('Plain curd', 200, 'g'), food('Seasonal vegetables', 200, 'g'), food('Fresh salad', 150, 'g')]),
        meal('Pre-workout snack', 'Roasted chana & banana', 290, 12, 55, 4, 11, 16, [food('Roasted chana', 50, 'g'), food('Banana', 1, 'medium')]),
        meal('Recovery', 'Eggs & milk', 290, 22, 15, 16, 0, 34, [food('Whole eggs', 2, 'whole'), food('Toned milk', 250, 'ml')]),
        meal('Dinner', 'Egg curry, rice, dal & vegetables', 760, 40, 108, 20, 16, 67, [food('Whole eggs', 3, 'whole'), food('Rice', 70, 'g raw'), food('Dal', 40, 'g raw'), food('Seasonal vegetables', 250, 'g'), food('Cooking oil', 5, 'ml')])
      ]
    },
    nonveg: {
      booster: { name: 'Lean chicken protein top-up', quantity: 100, unit: 'g raw', calories: 120, protein: 23, carbs: 0, fat: 3, fibre: 0, cost: 35 },
      meals: [
        meal('Breakfast', 'Egg bhurji & vegetable poha', 580, 29, 78, 19, 9, 48, [food('Whole eggs', 3, 'whole'), food('Poha', 80, 'g raw'), food('Mixed vegetables', 120, 'g'), food('Cooking oil', 5, 'ml')]),
        meal('Lunch', 'Chicken, rice, vegetables & salad', 720, 50, 92, 16, 13, 86, [food('Lean chicken', 180, 'g raw'), food('Rice', 80, 'g raw'), food('Seasonal vegetables', 200, 'g'), food('Fresh salad', 150, 'g'), food('Cooking oil', 5, 'ml')]),
        meal('Pre-workout snack', 'Roasted chana & banana', 290, 12, 55, 4, 11, 16, [food('Roasted chana', 50, 'g'), food('Banana', 1, 'medium')]),
        meal('Recovery', 'Curd & milk', 285, 19, 27, 11, 0, 31, [food('Plain curd', 250, 'g'), food('Toned milk', 250, 'ml')]),
        meal('Dinner', 'Chicken, roti, dal & vegetables', 740, 53, 82, 19, 19, 91, [food('Lean chicken', 150, 'g raw'), food('Whole-wheat atta', 60, 'g raw'), food('Dal', 40, 'g raw'), food('Seasonal vegetables', 250, 'g'), food('Cooking oil', 5, 'ml')])
      ]
    }
  };

  function food(name, quantity, unit) {
    return { name, quantity, unit };
  }

  function meal(type, name, calories, protein, carbs, fat, fibre, cost, foods) {
    return { type, name, calories, protein, carbs, fat, fibre, cost, foods };
  }

  function round(value, step) {
    return Math.round(value / step) * step;
  }

  function nearestPracticalBudget(estimatedCost, enteredBudget) {
    const estimate = Math.max(0, Number(estimatedCost) || 0);
    const entered = Math.max(0, Number(enteredBudget) || 0);
    if (estimate <= entered) return entered;
    return Math.ceil(estimate / 10) * 10;
  }

  function calculateTargets(profile) {
    const heightM = profile.height / 100;
    const bmi = profile.weight / (heightM * heightM);
    const sexConstant = profile.sex === 'male' ? 5 : -161;
    const rmr = (10 * profile.weight) + (6.25 * profile.height) - (5 * profile.age) + sexConstant;
    const activityFactor = activityFactors[profile.activity] + (gymDayAdjustments[profile.gymDays] || 0);
    const tdee = rmr * activityFactor;
    const goalRule = goalRules[profile.goal];
    const calories = round(tdee * goalRule.calorieFactor, 50);
    const bmiReferenceWeight = 23 * heightM * heightM;
    const proteinWeight = bmi >= 27.5 ? Math.min(profile.weight, bmiReferenceWeight) : profile.weight;
    const protein = Math.round(proteinWeight * goalRule.proteinFactor);
    const fat = Math.round((calories * 0.27) / 9);
    const carbs = Math.max(0, Math.round((calories - (protein * 4) - (fat * 9)) / 4));
    return { bmi, rmr, tdee, calories, protein, fat, carbs, fibre: 25, proteinWeight, goalRule, activityFactor };
  }

  function sumMeals(meals) {
    return meals.reduce((total, item) => {
      total.calories += item.calories;
      total.protein += item.protein;
      total.carbs += item.carbs;
      total.fat += item.fat;
      total.fibre += item.fibre;
      total.cost += item.cost;
      return total;
    }, { calories: 0, protein: 0, carbs: 0, fat: 0, fibre: 0, cost: 0 });
  }

  function scaledFood(item, scale) {
    return { ...item, quantity: item.quantity * scale };
  }

  function scaledMeal(item, scale) {
    return {
      ...item,
      calories: item.calories * scale,
      protein: item.protein * scale,
      carbs: item.carbs * scale,
      fat: item.fat * scale,
      fibre: item.fibre * scale,
      cost: item.cost * scale,
      foods: item.foods.map((entry) => scaledFood(entry, scale))
    };
  }

  function buildPlan(profile, targets) {
    const library = mealLibrary[profile.diet];
    const base = sumMeals(library.meals);
    let boosterCount = 0;
    let scale = targets.calories / base.calories;
    let projectedProtein = base.protein * scale;

    while (projectedProtein < targets.protein * 0.95 && boosterCount < 5) {
      boosterCount += 1;
      scale = (targets.calories - (boosterCount * library.booster.calories)) / base.calories;
      projectedProtein = (base.protein * scale) + (boosterCount * library.booster.protein);
    }

    if (scale < 0.5 || scale > 1.65 || projectedProtein < targets.protein * 0.88) {
      return { blocked: true, reason: 'This profile falls outside the safe portion range of the current meal library. Please ask a qualified dietitian or New Gym coach for a manual plan.' };
    }

    let meals = library.meals.map((item) => scaledMeal(item, scale));
    if (boosterCount > 0) {
      const recovery = meals.find((item) => item.type === 'Recovery');
      const booster = library.booster;
      recovery.foods.push({ name: booster.name, quantity: booster.quantity * boosterCount, unit: booster.unit });
      recovery.calories += booster.calories * boosterCount;
      recovery.protein += booster.protein * boosterCount;
      recovery.carbs += booster.carbs * boosterCount;
      recovery.fat += booster.fat * boosterCount;
      recovery.fibre += booster.fibre * boosterCount;
      recovery.cost += booster.cost * boosterCount;
    }

    meals = reshapeMeals(meals, profile.meals, profile.workout, profile.gymDays);
    const totals = sumMeals(meals);
    return { blocked: false, meals, totals, scale, boosterCount };
  }

  function mergeMeals(first, second, type) {
    return {
      type,
      name: first.name + ' + ' + second.name,
      calories: first.calories + second.calories,
      protein: first.protein + second.protein,
      carbs: first.carbs + second.carbs,
      fat: first.fat + second.fat,
      fibre: first.fibre + second.fibre,
      cost: first.cost + second.cost,
      foods: [...first.foods, ...second.foods]
    };
  }

  function retimeMeal(item, type) {
    return { ...item, type };
  }

  function reshapeMeals(meals, desiredMeals, workout, gymDays) {
    const [breakfast, lunch, snack, recovery, dinner] = meals;
    if (gymDays === 0) {
      const neutral = [retimeMeal(breakfast, 'Breakfast'), retimeMeal(lunch, 'Lunch'), retimeMeal(snack, 'Snack'), retimeMeal(recovery, 'Protein snack'), retimeMeal(dinner, 'Dinner')];
      if (desiredMeals === 5) return neutral;
      if (desiredMeals === 4) return [neutral[0], neutral[1], mergeMeals(neutral[2], neutral[3], 'Afternoon snack'), neutral[4]];
      return [neutral[0], mergeMeals(neutral[1], neutral[2], 'Lunch'), mergeMeals(neutral[3], neutral[4], 'Dinner')];
    }
    if (workout === 'morning') {
      if (desiredMeals === 5) return [retimeMeal(snack, 'Pre-workout snack'), retimeMeal(breakfast, 'Post-workout breakfast'), retimeMeal(recovery, 'Mid-morning protein snack'), retimeMeal(lunch, 'Lunch'), retimeMeal(dinner, 'Dinner')];
      if (desiredMeals === 4) return [retimeMeal(snack, 'Pre-workout snack'), mergeMeals(breakfast, recovery, 'Post-workout breakfast'), retimeMeal(lunch, 'Lunch'), retimeMeal(dinner, 'Dinner')];
      return [mergeMeals(snack, breakfast, 'Morning workout meal'), mergeMeals(recovery, lunch, 'Lunch + protein'), retimeMeal(dinner, 'Dinner')];
    }
    if (desiredMeals === 5) return [retimeMeal(breakfast, 'Breakfast'), retimeMeal(lunch, 'Lunch'), retimeMeal(snack, 'Pre-workout snack'), retimeMeal(recovery, 'Post-workout recovery'), retimeMeal(dinner, 'Dinner')];
    if (desiredMeals === 4) return [retimeMeal(breakfast, 'Breakfast'), retimeMeal(lunch, 'Lunch'), retimeMeal(snack, 'Pre-workout snack'), mergeMeals(recovery, dinner, 'Post-workout dinner')];
    return [retimeMeal(breakfast, 'Breakfast'), mergeMeals(lunch, snack, 'Lunch + pre-workout'), mergeMeals(recovery, dinner, 'Post-workout dinner')];
  }

  function numericFormValue(values, name) {
    const raw = values.get(name);
    return raw === null || String(raw).trim() === '' ? NaN : Number(raw);
  }

  function readProfile() {
    const values = new FormData(form);
    return {
      age: numericFormValue(values, 'age'), sex: String(values.get('sex') || ''),
      weight: numericFormValue(values, 'weight'), height: numericFormValue(values, 'height'),
      goal: String(values.get('goal') || ''), activity: String(values.get('activity') || ''),
      gymDays: numericFormValue(values, 'gymDays'), diet: String(values.get('diet') || ''),
      budget: numericFormValue(values, 'budget'), meals: numericFormValue(values, 'meals'),
      workout: String(values.get('workout') || ''), safety: values.get('safety') === 'on'
    };
  }

  function validateProfile(profile) {
    if (!Number.isInteger(profile.age) || profile.age < 18 || profile.age > 65) return 'Enter an age between 18 and 65 years.';
    if (!['male', 'female'].includes(profile.sex)) return 'Choose sex for the calorie estimate.';
    if (!Number.isFinite(profile.weight) || profile.weight < 35 || profile.weight > 200) return 'Enter a weight between 35 and 200 kg.';
    if (!Number.isFinite(profile.height) || profile.height < 135 || profile.height > 215) return 'Enter a height between 135 and 215 cm.';
    if (!goalRules[profile.goal]) return 'Choose your primary fitness goal.';
    if (!activityFactors[profile.activity]) return 'Choose your usual daily activity level.';
    if (!Object.prototype.hasOwnProperty.call(gymDayAdjustments, profile.gymDays)) return 'Choose your gym days per week.';
    if ((profile.goal === 'gain' || profile.goal === 'recomp') && profile.gymDays === 0) return 'Muscle building and body recomposition require regular resistance training. Choose at least 1–2 gym days or select a different goal.';
    if (!mealLibrary[profile.diet]) return 'Choose your diet preference.';
    const minimumBudget = minimumBudgetByDiet[profile.diet] || 100;
    if (!Number.isFinite(profile.budget) || profile.budget < minimumBudget || profile.budget > 1000) return 'Enter a daily food budget between ₹' + minimumBudget + ' and ₹1,000 for this diet preference.';
    if (![3, 4, 5].includes(profile.meals)) return 'Choose 3, 4 or 5 meals per day.';
    if (profile.gymDays === 0 && profile.workout !== 'none') return 'Choose “Not applicable” for workout time when you are not currently training.';
    if (profile.gymDays > 0 && !['morning', 'afternoon', 'evening'].includes(profile.workout)) return 'Choose your usual workout time.';
    if (!profile.safety) return 'Confirm the safety statement before creating an automatic plan.';
    const bmi = profile.weight / Math.pow(profile.height / 100, 2);
    if (bmi < 18.5) return 'Because the entered BMI is below 18.5, please seek an individual assessment instead of using an automatic fitness diet.';
    if (bmi >= 35) return 'Because the entered BMI is 35 or above, please seek an individual clinical assessment before using an automatic calorie target.';
    return '';
  }

  function bmiLabel(bmi) {
    if (bmi < 18.5) return 'below screening range';
    if (bmi < 23) return 'desirable screening range';
    if (bmi < 27.5) return 'increased-risk screening range';
    return 'high-risk screening range';
  }

  function workoutCopy(profile) {
    if (profile.gymDays === 0) return 'No workout timing is applied. Distribute these meals at times that suit your day.';
    const timing = profile.workout === 'morning' ? 'morning' : profile.workout === 'afternoon' ? 'afternoon' : 'evening';
    return 'For a ' + timing + ' workout, keep the pre-workout meal comfortable and use the recovery meal after training. Total daily intake matters more than an exact minute-by-minute schedule.';
  }

  function formatQuantity(item) {
    let quantity;
    if (item.unit === 'whole' || item.unit === 'medium') quantity = Math.max(0.5, Math.round(item.quantity * 2) / 2);
    else if (item.quantity < 20) quantity = Math.round(item.quantity);
    else quantity = round(item.quantity, 5);
    return quantity + ' ' + item.unit;
  }

  function pdfAscii(text) {
    return String(text)
      .replace(/\u20B9/g, 'Rs. ')
      .replace(/[\u2013\u2014]/g, '-')
      .replace(/\u2248/g, 'approx. ')
      .replace(/\u2194/g, '<->')
      .replace(/[\u201C\u201D]/g, '"')
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[^\x20-\x7E]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function wrapPdfLine(text, maxLength) {
    const clean = pdfAscii(text);
    if (!clean) return [''];
    const limit = maxLength || 82;
    const words = clean.split(' ');
    const lines = [];
    let line = '';
    words.forEach((word) => {
      if (!line) {
        line = word;
      } else if ((line + ' ' + word).length <= limit) {
        line += ' ' + word;
      } else {
        lines.push(line);
        line = word;
      }
    });
    if (line) lines.push(line);
    return lines;
  }

  function buildPlanDownloadLines(profile, targets, plan) {
    const totals = plan.totals;
    const estimatedCost = Math.ceil(totals.cost);
    const lines = [
      'NEW GYM - PERSONALISED INDIAN DIET PLAN',
      'Location to be configured',
      '',
      'PLAN SUMMARY',
      'Goal: ' + targets.goalRule.label,
      'Profile: ' + profile.age + ' years | ' + (profile.sex === 'male' ? 'Male' : 'Female') + ' | ' + profile.weight + ' kg | ' + profile.height + ' cm',
      'Diet: ' + dietLabels[profile.diet] + ' | Meals: ' + profile.meals + '/day | BMI: ' + targets.bmi.toFixed(1) + ' (' + bmiLabel(targets.bmi) + ')',
      'Estimated maintenance: ' + round(targets.tdee, 50).toLocaleString('en-IN') + ' kcal/day',
      'Starting calorie target: ' + targets.calories.toLocaleString('en-IN') + ' kcal/day',
      'Generated plan: ' + Math.round(totals.calories) + ' kcal | ' + Math.round(totals.protein) + ' g protein | ' + Math.round(totals.carbs) + ' g carbs | ' + Math.round(totals.fat) + ' g fat | ' + Math.round(totals.fibre) + ' g fibre',
      'Food budget: approx. Rs. ' + estimatedCost + '/day (selected budget Rs. ' + profile.budget + '/day)',
      '',
      'WORKOUT TIMING',
      workoutCopy(profile),
      '',
      'ONE-DAY INDIAN MEAL STRUCTURE'
    ];

    plan.meals.forEach((item, index) => {
      lines.push('');
      lines.push('MEAL ' + (index + 1) + ' - ' + item.type.toUpperCase());
      lines.push(item.name + ' | approx. Rs. ' + Math.round(item.cost));
      item.foods.forEach((entry) => lines.push('- ' + entry.name + ': ' + formatQuantity(entry)));
      lines.push('Approx. nutrition: ' + Math.round(item.calories) + ' kcal | ' + Math.round(item.protein) + ' g protein | ' + Math.round(item.carbs) + ' g carbs | ' + Math.round(item.fibre) + ' g fibre');
    });

    const proteinChoices = {
      vegetarian: 'Soya chunks <-> dal + curd <-> paneer <-> tofu',
      eggetarian: 'Eggs <-> soya chunks <-> dal + curd <-> paneer',
      nonveg: 'Lean chicken <-> eggs <-> local fish <-> dal + curd',
      vegan: 'Soya chunks <-> tofu <-> dal <-> chana or rajma'
    };
    lines.push('', 'PRACTICAL FOOD SWAPS');
    lines.push('Protein: ' + proteinChoices[profile.diet]);
    lines.push('Grain/starch: Rice <-> roti <-> poha <-> oats <-> dalia or millet');
    lines.push('Fruit: Banana <-> guava <-> orange <-> papaya <-> seasonal fruit');
    lines.push('', 'IMPORTANT NOTES');
    lines.push('Ingredient weights are approximate raw quantities unless a cooked item or household serving is explicitly stated. Nutrition and local food costs naturally vary by recipe, brand and preparation.');
    lines.push('Aim for vegetables and fruit across the day. Prefer whole grains, millets, pulses and minimally processed foods. Use iodised salt sparingly and keep fried or packaged foods occasional.');
    lines.push('Track progress using trends over 2-3 weeks and review hunger, energy and gym performance before changing calories.');
    lines.push('', 'SAFETY DISCLAIMER');
    lines.push('This is an automatic general fitness nutrition starting structure for healthy adults, not medical advice or a prescription. Pregnancy or breastfeeding, kidney or liver disease, medicated diabetes, eating-disorder history, major food allergy, prescribed medical diets, or other clinical nutrition needs require individual professional advice.');
    const gym = window.NEW_GYM_CONFIG || {};
    const contactBits = [gym.name || 'New Gym', gym.phoneDisplay || '', gym.address || ''].filter(Boolean);
    lines.push('', contactBits.join(' | '));

    return lines.flatMap((line) => wrapPdfLine(line, 82));
  }

  function pdfEscape(text) {
    return pdfAscii(text).replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
  }

  function buildSimplePdfDocument(lines) {
    const linesPerPage = 48;
    const pages = [];
    for (let index = 0; index < lines.length; index += linesPerPage) pages.push(lines.slice(index, index + linesPerPage));
    const objects = [];
    objects[1] = '<< /Type /Catalog /Pages 2 0 R >>';
    objects[3] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';
    const kids = [];

    pages.forEach((pageLines, pageIndex) => {
      const pageObject = 4 + (pageIndex * 2);
      const contentObject = pageObject + 1;
      kids.push(pageObject + ' 0 R');
      const commands = ['BT', '/F1 10 Tf', '46 800 Td', '14 TL'];
      pageLines.forEach((line) => {
        commands.push('(' + pdfEscape(line) + ') Tj');
        commands.push('T*');
      });
      commands.push('ET');
      const stream = commands.join('\n');
      objects[pageObject] = '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents ' + contentObject + ' 0 R >>';
      objects[contentObject] = '<< /Length ' + stream.length + ' >>\nstream\n' + stream + '\nendstream';
    });

    objects[2] = '<< /Type /Pages /Kids [' + kids.join(' ') + '] /Count ' + pages.length + ' >>';
    let pdf = '%PDF-1.4\n% New Gym Diet Plan\n';
    const offsets = [0];
    for (let index = 1; index < objects.length; index += 1) {
      offsets[index] = pdf.length;
      pdf += index + ' 0 obj\n' + objects[index] + '\nendobj\n';
    }
    const xrefOffset = pdf.length;
    pdf += 'xref\n0 ' + objects.length + '\n0000000000 65535 f \n';
    for (let index = 1; index < objects.length; index += 1) pdf += String(offsets[index]).padStart(10, '0') + ' 00000 n \n';
    pdf += 'trailer\n<< /Size ' + objects.length + ' /Root 1 0 R >>\nstartxref\n' + xrefOffset + '\n%%EOF\n';
    return pdf;
  }

  if (typeof document === 'undefined') {
    if (typeof module !== 'undefined' && module.exports) {
      module.exports = { calculateTargets, buildPlan, validateProfile, bmiLabel, nearestPracticalBudget, buildPlanDownloadLines, buildSimplePdfDocument };
    }
    return;
  }

  const form = document.getElementById('diet-form');
  const status = document.getElementById('planner-status');
  const result = document.getElementById('plan-result');
  const resultContent = document.getElementById('result-content');
  const resultAlert = document.getElementById('result-alert');
  const downloadButton = document.getElementById('download-plan');
  let downloadablePlan = null;

  function clearElement(element) {
    element.replaceChildren();
  }

  function appendTextElement(parent, tag, text, className) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
  }

  function renderProfile(profile, targets) {
    const strip = document.getElementById('profile-strip');
    clearElement(strip);
    const labels = [
      profile.age + ' years',
      profile.sex === 'male' ? 'Male' : 'Female',
      profile.weight + ' kg',
      profile.height + ' cm',
      dietLabels[profile.diet],
      profile.meals + ' meals/day',
      'BMI ' + targets.bmi.toFixed(1) + ' · ' + bmiLabel(targets.bmi)
    ];
    labels.forEach((label) => appendTextElement(strip, 'span', label));
  }

  function renderTargets(targets, plan) {
    const grid = document.getElementById('target-grid');
    clearElement(grid);
    const actualCalories = Math.round(plan.totals.calories);
    const actualProtein = Math.round(plan.totals.protein);
    const actualCarbs = Math.round(plan.totals.carbs);
    const actualFat = Math.round(plan.totals.fat);
    const actualFibre = Math.round(plan.totals.fibre);
    const items = [
      ['Calories', targets.calories.toLocaleString('en-IN') + ' kcal', 'plan ≈ ' + actualCalories.toLocaleString('en-IN') + ' kcal'],
      ['Protein', actualProtein + ' g', 'goal ≈ ' + targets.protein + ' g'],
      ['Carbohydrate', actualCarbs + ' g', 'from generated food portions'],
      ['Fat', actualFat + ' g', 'from generated food portions'],
      ['Fibre', actualFibre + ' g', 'aim for at least 25 g/day']
    ];
    items.forEach(([label, value, note]) => {
      const card = document.createElement('article');
      card.className = 'target-card';
      appendTextElement(card, 'span', label);
      appendTextElement(card, 'strong', value);
      appendTextElement(card, 'small', note);
      grid.appendChild(card);
    });
  }

  function renderMeals(plan) {
    const grid = document.getElementById('meal-grid');
    clearElement(grid);
    plan.meals.forEach((item, index) => {
      const card = document.createElement('article');
      card.className = 'meal-card';
      const head = document.createElement('div');
      head.className = 'meal-card__head';
      const title = document.createElement('div');
      appendTextElement(title, 'span', 'Meal ' + (index + 1) + ' · ' + item.type);
      appendTextElement(title, 'h4', item.name);
      head.appendChild(title);
      appendTextElement(head, 'strong', '≈ ₹' + Math.round(item.cost));
      card.appendChild(head);

      const foods = document.createElement('ul');
      foods.className = 'meal-foods';
      item.foods.forEach((entry) => {
        const row = document.createElement('li');
        appendTextElement(row, 'span', entry.name);
        appendTextElement(row, 'span', formatQuantity(entry));
        foods.appendChild(row);
      });
      card.appendChild(foods);

      const macros = document.createElement('div');
      macros.className = 'meal-macros';
      [Math.round(item.calories) + ' kcal', Math.round(item.protein) + ' g protein', Math.round(item.carbs) + ' g carbs', Math.round(item.fibre) + ' g fibre'].forEach((value) => appendTextElement(macros, 'span', value));
      card.appendChild(macros);
      grid.appendChild(card);
    });
  }

  function renderSwaps(profile) {
    const proteinChoices = {
      vegetarian: 'Soya chunks ↔ dal + curd ↔ paneer ↔ tofu',
      eggetarian: 'Eggs ↔ soya chunks ↔ dal + curd ↔ paneer',
      nonveg: 'Lean chicken ↔ eggs ↔ local fish ↔ dal + curd',
      vegan: 'Soya chunks ↔ tofu ↔ dal ↔ chana or rajma'
    };
    const swaps = [
      ['Protein source', proteinChoices[profile.diet]],
      ['Grain or starch', 'Rice ↔ roti ↔ poha ↔ oats ↔ dalia or millet'],
      ['Fruit choice', 'Banana ↔ guava ↔ orange ↔ papaya ↔ seasonal fruit']
    ];
    const grid = document.getElementById('swap-grid');
    clearElement(grid);
    swaps.forEach(([label, choices]) => {
      const card = document.createElement('article');
      card.className = 'swap-card';
      appendTextElement(card, 'strong', label);
      appendTextElement(card, 'span', choices);
      grid.appendChild(card);
    });
  }

  function showBlocked(title, summary, message) {
    document.getElementById('print-plan').hidden = true;
    downloadButton.hidden = true;
    downloadablePlan = null;
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-summary').textContent = summary;
    resultContent.hidden = true;
    resultAlert.hidden = false;
    clearElement(resultAlert);
    appendTextElement(resultAlert, 'strong', 'A safe automatic plan was not generated.');
    appendTextElement(resultAlert, 'span', message);
    result.hidden = false;
    result.focus({ preventScroll: true });
    result.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  function renderResult(profile, targets, plan) {
    const estimatedCost = Math.ceil(plan.totals.cost);
    document.getElementById('result-title').textContent = targets.goalRule.label;
    document.getElementById('result-summary').textContent = 'Estimated maintenance: ' + round(targets.tdee, 50).toLocaleString('en-IN') + ' kcal/day. This starting target is approximately ' + targets.calories.toLocaleString('en-IN') + ' kcal/day.';

    const enteredBudget = profile.budget;
    const adjustedBudget = nearestPracticalBudget(estimatedCost, enteredBudget);
    const budgetWasAdjusted = adjustedBudget > enteredBudget;
    if (budgetWasAdjusted) {
      profile.budget = adjustedBudget;
      budgetInput.value = String(adjustedBudget);
      status.textContent = 'Budget automatically adjusted from ₹' + enteredBudget + ' to about ₹' + adjustedBudget + '/day so this plan can be generated.';
      status.dataset.state = 'success';
    }

    resultAlert.hidden = true;
    resultContent.hidden = false;
    document.getElementById('print-plan').hidden = false;
    downloadButton.hidden = false;
    renderProfile(profile, targets);
    renderTargets(targets, plan);
    renderMeals(plan);
    renderSwaps(profile);

    const budgetPercent = Math.min(100, Math.round((estimatedCost / profile.budget) * 100));
    document.getElementById('budget-copy').textContent = budgetWasAdjusted
      ? 'Approximate home-cooked ingredient estimate using illustrative local prices. Your entered ₹' + enteredBudget + ' budget was below the recipe estimate, so the planner selected the next practical budget of about ₹' + profile.budget + '/day.'
      : 'Approximate home-cooked ingredient estimate using illustrative local prices. Your ₹' + profile.budget + ' limit leaves about ₹' + (profile.budget - estimatedCost) + ' of buffer.';
    document.getElementById('budget-total').textContent = '≈ ₹' + estimatedCost + '/day';
    document.getElementById('budget-meter-fill').style.width = budgetPercent + '%';
    document.getElementById('workout-note').textContent = workoutCopy(profile);
    downloadablePlan = { profile: { ...profile }, targets, plan };
    window.gravityAnalytics?.event('diet_plan_generated');

    result.hidden = false;
    result.focus({ preventScroll: true });
    result.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  const dietSelect = document.getElementById('diet-type');
  const budgetInput = document.getElementById('diet-budget');
  const budgetHelp = document.getElementById('diet-budget-help');
  const gymDaysSelect = document.getElementById('diet-days');
  const workoutSelect = document.getElementById('diet-workout');

  function updateBudgetGuidance() {
    const diet = dietSelect.value;
    const minimum = minimumBudgetByDiet[diet] || 100;
    budgetInput.min = String(minimum);
    budgetHelp.textContent = diet
      ? 'Current ' + dietLabels[diet].toLowerCase() + ' meal library starts around ₹' + minimum + '/day. If your profile needs more, the planner will automatically choose the next practical budget.'
      : 'Current meal library starts around ₹100–₹150/day depending on diet. If needed, the planner automatically moves to the next practical budget.';
  }

  function syncWorkoutTime() {
    if (gymDaysSelect.value === '0') workoutSelect.value = 'none';
    else if (workoutSelect.value === 'none') workoutSelect.value = 'evening';
  }

  function focusValidationProblem(message) {
    const rules = [
      [/age/i, 'diet-age'], [/sex/i, 'diet-sex'], [/weight/i, 'diet-weight'], [/height/i, 'diet-height'],
      [/primary fitness goal/i, 'diet-goal'], [/daily activity/i, 'diet-activity'], [/gym days|resistance training|recomposition/i, 'diet-days'],
      [/diet preference|food budget/i, message.includes('budget') ? 'diet-budget' : 'diet-type'], [/meals per day/i, 'diet-meals'],
      [/workout time|Not applicable/i, 'diet-workout'], [/safety/i, 'diet-safety']
    ];
    const found = rules.find(([pattern]) => pattern.test(message));
    if (found) document.getElementById(found[1])?.focus();
  }

  function invalidateVisibleResult() {
    downloadablePlan = null;
    if (result.hidden) return;
    result.hidden = true;
    status.textContent = 'Your inputs changed. Create a new plan to refresh the result.';
    status.dataset.state = '';
  }

  dietSelect.addEventListener('change', updateBudgetGuidance);
  gymDaysSelect.addEventListener('change', syncWorkoutTime);
  form.addEventListener('input', invalidateVisibleResult);
  form.addEventListener('change', invalidateVisibleResult);
  updateBudgetGuidance();
  syncWorkoutTime();

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    status.textContent = '';
    status.dataset.state = '';
    result.hidden = true;
    downloadablePlan = null;

    const profile = readProfile();
    const error = validateProfile(profile);
    if (error) {
      status.textContent = error;
      status.dataset.state = 'error';
      focusValidationProblem(error);
      return;
    }

    const targets = calculateTargets(profile);
    const calorieFloor = profile.sex === 'female' ? 1400 : 1600;
    if (targets.calories < calorieFloor || targets.calories > 3800) {
      showBlocked('Your profile needs an individual review', 'The estimated calorie target falls outside this planner’s conservative automatic range.', 'Please ask a registered dietitian or qualified healthcare professional to assess an appropriate energy target for you.');
      return;
    }

    const plan = buildPlan(profile, targets);
    if (plan.blocked) {
      showBlocked('Your profile needs an individual review', 'The current Indian meal library cannot create a sufficiently balanced match for these inputs.', plan.reason);
      return;
    }

    renderResult(profile, targets, plan);
  });

  downloadButton.addEventListener('click', () => {
    if (!downloadablePlan) return;
    window.gravityAnalytics?.event('diet_plan_pdf_download');
    const lines = buildPlanDownloadLines(downloadablePlan.profile, downloadablePlan.targets, downloadablePlan.plan);
    const pdf = buildSimplePdfDocument(lines);
    const blob = new Blob([pdf], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const date = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = 'gravity-indian-diet-plan-' + date + '.pdf';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  document.getElementById('print-plan').addEventListener('click', () => {
    window.gravityAnalytics?.event('diet_plan_print');
    window.print();
  });
  document.getElementById('reset-plan').addEventListener('click', () => {
    form.reset();
    result.hidden = true;
    downloadablePlan = null;
    status.textContent = '';
    status.dataset.state = '';
    updateBudgetGuidance();
    syncWorkoutTime();
    form.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    document.getElementById('diet-age').focus();
  });
})();
