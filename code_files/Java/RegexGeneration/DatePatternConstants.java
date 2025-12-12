package com.hcl.util;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

@Component
public class DatePatternConstants {

	
	public String getDatePattern(String key)
	{
		Map<String,String> datePattern = new HashMap<String,String> ();
		datePattern.put("yyyy-MM-dd HH:mm:ss,SSS", "([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:([0-5][0-9]),([0-9]{3})");
		datePattern.put("MM-DD-YYYY", "(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-([0-9]{4})");
		datePattern.put("yyyy-MM-DD", "([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])");
		datePattern.put("MM-DD-YYYY HH:MM:SS", "(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-([0-9]{4}) (2[0-3]|[01][0-9]):[0-5][0-9]:([0-5][0-9])");
		datePattern.put("yyyy-MM-dd HH:mm:ss", "([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:([0-5][0-9])");
		datePattern.put("YYYY-MM-DD HH:MM", "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]");
		datePattern.put("MM-DD-YYYY  HH:MM", "(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-[0-9]{4} (2[0-3]|[01][0-9]):[0-5][0-9]");
		datePattern.put("dd/MMM/YYYY", "^([01][0-9]|[1-2][0-9]|3[0-1])//(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)//[0-9]{4}");
		datePattern.put("dd/MMM/yyyy:HH:mm:ss", "^([01][0-9]|[1-2][0-9]|3[0-1])//(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)//[0-9]{4}:(2[0-3]|[01][0-9]):[0-5][0-9]:([0-5][0-9])");
		
		String regex = datePattern.get(key);
		
		return regex;
		
	}
	public String getLogType()
	{
		String regex = "(?i)(DEBUG|ERROR|LEVEL|FATAL|WARN|INFO)";
		
		return regex;
		
	}
}
