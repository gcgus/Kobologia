function findAllZonesWithSameKey(rootKey,g)
    local zonesWithSameKeyIdx = {}
    for n,z in pairs(g.zones) do
        if z.rootKey == rootKey then
            table.insert(zonesWithSameKeyIdx, n)
        end
    end
    return zonesWithSameKeyIdx
end

if not instrument then
    print("No hay instrumento para sincronizar")
end

--Path de los samples
local path = scriptPath .. filesystem.preferred("/cut")
print("Samples en " .. path)

--GRUPOS
instrument.groups:reset()

for i = 0,24 do
    instrument.groups:add(Group())
	instrument.groups[i].name=tostring(i)
end

local samples = {}

local i = 1
for _,p in filesystem.directoryRecursive(path) do
    if filesystem.isRegularFile(p) then
      if filesystem.extension(p) == '.wav' or filesystem.extension(p) == '.aif' or filesystem.extension(p) == '.aiff' then
        samples[i] = p
        i = i+1
      end
    end
end

local keys = {}

for i = 0,3 do
	current=samples[(i*26)+1]
	print("Sample = " .. current)
	current_pitch = mir.detectPitch(current)
	print("Pitch = " .. current_pitch)
	nearest_key = math.floor( current_pitch + 0.5 )
	print("Frecuencia de la nota mas cercana = " .. nearest_key)
			
	keys[nearest_key] = nearest_key


	for k,g in pairs(instrument.groups) do
		current = samples[(i*26)+1+k]
		print("Sample = " .. current)
	    local z = Zone()
	    g.zones:add(z)
		
		z.file = current
		
		z.rootKey       = nearest_key
		z.keyRange.low  = nearest_key
		z.keyRange.high = nearest_key

		z.tune = nearest_key - current_pitch
		
		z.velocityRange.low = 0
		z.velocityRange.high = 127
		
		z.loops:resize(1)
		z.loops[0].start=0
		z.loops[0].mode = 1
		z.loops[0].tune = 0
		z.loops[0].length = z.sampleEnd
		print(z.sampleEnd)
		print("####################")
		print(z.loops[0].mode)
		print(z.loops[0].start)
		print(z.loops[0].length)
		print(z.loops[0].xfade)

		print(z.loops[0].count)
		print(z.loops[0].tune)


				
	end

	
end


local tkeys = {}
for k in pairs(keys) do table.insert(tkeys, k) end

table.sort(tkeys)


for k,g in pairs(instrument.groups) do
	local keyRangeLow = tkeys[1]
	for n,key in pairs(tkeys) do

		if n<#tkeys then
			keyRangeHigh = math.floor((tkeys[n+1] + key)/2)
		else
			keyRangeHigh = key
		end

		zonesWithSameKeyIdx = findAllZonesWithSameKey(key,g)

		for _, index in pairs(zonesWithSameKeyIdx) do
			g.zones[index].keyRange.high = keyRangeHigh
			g.zones[index].keyRange.low  = keyRangeLow
		end

		keyRangeLow = keyRangeHigh + 1
	end
end